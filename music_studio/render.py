from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

import numpy as np

from .models import Note, Project, Track
from .theory import beats_per_bar

PPQ = 480


def midi_frequency(pitch: int) -> float:
    return 440.0 * (2.0 ** ((pitch - 69) / 12.0))


def _waveform(instrument: str, phase: np.ndarray) -> np.ndarray:
    name = instrument.lower()
    if name in {"strings", "violin", "cello", "pad"}:
        return 0.7 * np.sin(phase) + 0.2 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)
    if name in {"bass"}:
        return 0.75 * np.sin(phase) + 0.25 * np.sin(phase / 2)
    if name in {"synth", "lead"}:
        return (2 / math.pi) * np.arcsin(np.sin(phase))
    return np.sin(phase) + 0.22 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)


def _envelope(length: int, sample_rate: int) -> np.ndarray:
    if length <= 0:
        return np.zeros(0, dtype=np.float32)
    attack = min(length, max(1, int(sample_rate * 0.012)))
    release = min(length - attack, max(1, int(sample_rate * 0.08)))
    envelope = np.ones(length, dtype=np.float32)
    envelope[:attack] = np.linspace(0, 1, attack, endpoint=False, dtype=np.float32)
    if release > 0:
        envelope[-release:] = np.linspace(1, 0, release, endpoint=True, dtype=np.float32)
    return envelope


def render_wav(project: Project, target: Path) -> Path:
    seconds_per_beat = 60.0 / project.tempo
    project_beats = beats_per_bar(project.time_signature) * project.bars
    end_beat = max(
        [project_beats]
        + [note.start + note.duration for track in project.tracks for note in track.notes]
    )
    duration_seconds = end_beat * seconds_per_beat + 0.25
    sample_count = max(1, int(duration_seconds * project.sample_rate))
    left = np.zeros(sample_count, dtype=np.float32)
    right = np.zeros(sample_count, dtype=np.float32)

    for track in project.tracks:
        left_gain = math.sqrt((1.0 - track.pan) / 2.0) * track.volume
        right_gain = math.sqrt((1.0 + track.pan) / 2.0) * track.volume
        for note in track.notes:
            start = int(note.start * seconds_per_beat * project.sample_rate)
            length = max(1, int(note.duration * seconds_per_beat * project.sample_rate))
            end = min(sample_count, start + length)
            length = end - start
            if length <= 0:
                continue
            time = np.arange(length, dtype=np.float32) / project.sample_rate
            phase = (2 * np.pi * midi_frequency(note.pitch) * time).astype(np.float32)
            signal = _waveform(track.instrument, phase).astype(np.float32)
            signal *= _envelope(length, project.sample_rate)
            signal *= (note.velocity / 127.0) * 0.22
            left[start:end] += signal * left_gain
            right[start:end] += signal * right_gain

    peak = float(max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-9))
    if peak > 0.98:
        left *= 0.98 / peak
        right *= 0.98 / peak
    stereo = np.column_stack((left, right))
    pcm = np.clip(stereo * 32767, -32768, 32767).astype("<i2")
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(project.sample_rate)
        wav.writeframes(pcm.tobytes())
    return target


def _varlen(value: int) -> bytes:
    buffer = value & 0x7F
    output = bytearray()
    while value >> 7:
        value >>= 7
        buffer <<= 8
        buffer |= (value & 0x7F) | 0x80
    while True:
        output.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(output)


def _midi_chunk(kind: bytes, payload: bytes) -> bytes:
    return kind + struct.pack(">I", len(payload)) + payload


def _tempo_track(project: Project) -> bytes:
    microseconds = round(60_000_000 / project.tempo)
    numerator, denominator = map(int, project.time_signature.split("/"))
    denominator_power = int(math.log2(denominator))
    payload = bytearray()
    payload += b"\x00\xff\x51\x03" + microseconds.to_bytes(3, "big")
    payload += b"\x00\xff\x58\x04" + bytes([numerator, denominator_power, 24, 8])
    payload += b"\x00\xff\x2f\x00"
    return _midi_chunk(b"MTrk", bytes(payload))


def _note_track(track: Track) -> bytes:
    events: list[tuple[int, int, bytes]] = []
    channel = track.channel & 0x0F
    events.append((0, 0, bytes([0xC0 | channel, track.program & 0x7F])))
    name = track.name.encode("utf-8")[:127]
    events.append((0, 1, b"\xff\x03" + _varlen(len(name)) + name))
    for note in track.notes:
        start = max(0, round(note.start * PPQ))
        end = max(start + 1, round((note.start + note.duration) * PPQ))
        events.append((start, 2, bytes([0x90 | channel, note.pitch, note.velocity])))
        events.append((end, 1, bytes([0x80 | channel, note.pitch, 0])))
    events.sort(key=lambda item: (item[0], item[1]))
    payload = bytearray()
    previous = 0
    for tick, _, event in events:
        payload += _varlen(tick - previous)
        payload += event
        previous = tick
    payload += b"\x00\xff\x2f\x00"
    return _midi_chunk(b"MTrk", bytes(payload))


def render_midi(project: Project, target: Path) -> Path:
    tracks = [_tempo_track(project)] + [_note_track(track) for track in project.tracks]
    header = _midi_chunk(b"MThd", struct.pack(">HHH", 1, len(tracks), PPQ))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(header + b"".join(tracks))
    return target


def _pitch_parts(pitch: int) -> tuple[str, int, int]:
    names = [
        ("C", 0), ("C", 1), ("D", 0), ("D", 1), ("E", 0), ("F", 0),
        ("F", 1), ("G", 0), ("G", 1), ("A", 0), ("A", 1), ("B", 0),
    ]
    step, alter = names[pitch % 12]
    octave = pitch // 12 - 1
    return step, alter, octave


def _append_musicxml_note(measure: Element, note: Note, chord: bool = False) -> None:
    node = SubElement(measure, "note")
    if chord:
        SubElement(node, "chord")
    pitch = SubElement(node, "pitch")
    step, alter, octave = _pitch_parts(note.pitch)
    SubElement(pitch, "step").text = step
    if alter:
        SubElement(pitch, "alter").text = str(alter)
    SubElement(pitch, "octave").text = str(octave)
    SubElement(node, "duration").text = str(max(1, round(note.duration * PPQ)))
    SubElement(node, "voice").text = "1"
    SubElement(node, "type").text = "quarter"
    velocity = SubElement(node, "velocity")
    velocity.text = str(note.velocity)


def render_musicxml(project: Project, target: Path) -> Path:
    score = Element("score-partwise", version="4.0")
    work = SubElement(score, "work")
    SubElement(work, "work-title").text = project.name
    part_list = SubElement(score, "part-list")
    numerator, denominator = map(int, project.time_signature.split("/"))
    beats = beats_per_bar(project.time_signature)

    for index, track in enumerate(project.tracks, start=1):
        score_part = SubElement(part_list, "score-part", id=f"P{index}")
        SubElement(score_part, "part-name").text = track.name

    for index, track in enumerate(project.tracks, start=1):
        part = SubElement(score, "part", id=f"P{index}")
        for bar in range(project.bars):
            measure = SubElement(part, "measure", number=str(bar + 1))
            if bar == 0:
                attributes = SubElement(measure, "attributes")
                SubElement(attributes, "divisions").text = str(PPQ)
                key = SubElement(attributes, "key")
                SubElement(key, "fifths").text = "0"
                time = SubElement(attributes, "time")
                SubElement(time, "beats").text = str(numerator)
                SubElement(time, "beat-type").text = str(denominator)
                clef = SubElement(attributes, "clef")
                SubElement(clef, "sign").text = "F" if track.instrument == "bass" else "G"
                SubElement(clef, "line").text = "4" if track.instrument == "bass" else "2"
                direction = SubElement(measure, "direction", placement="above")
                direction_type = SubElement(direction, "direction-type")
                metronome = SubElement(direction_type, "metronome")
                SubElement(metronome, "beat-unit").text = "quarter"
                SubElement(metronome, "per-minute").text = str(project.tempo)
                SubElement(direction, "sound", tempo=str(project.tempo))
            start = bar * beats
            end = start + beats
            notes = sorted(
                [note for note in track.notes if start <= note.start < end],
                key=lambda item: (item.start, item.pitch),
            )
            previous_start: float | None = None
            for note in notes:
                _append_musicxml_note(measure, note, chord=previous_start == note.start)
                previous_start = note.start

    indent(score)
    target.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(score).write(target, encoding="utf-8", xml_declaration=True)
    return target
