from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .models import Note, Project, Track

PITCH_CLASSES = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
}

PROGRAMS = {
    "piano": 0,
    "keys": 4,
    "strings": 48,
    "violin": 40,
    "cello": 42,
    "bass": 32,
    "synth": 81,
    "pad": 89,
    "lead": 80,
}


@dataclass(frozen=True)
class Key:
    root: int
    mode: str


def parse_key(value: str) -> Key:
    match = re.match(r"^\s*([A-Ga-g])([#b]?)(?:\s+)?(major|minor|maj|min|m)?\s*$", value)
    if not match:
        raise ValueError(f"unsupported key: {value}")
    letter, accidental, mode = match.groups()
    root_name = f"{letter.upper()}{accidental.upper()}"
    normalized_mode = "minor" if mode in {"minor", "min", "m"} else "major"
    return Key(root=PITCH_CLASSES[root_name], mode=normalized_mode)


def scale_pitches(key_name: str, low: int = 48, high: int = 84) -> list[int]:
    key = parse_key(key_name)
    intervals = SCALES[key.mode]
    return [pitch for pitch in range(low, high + 1) if (pitch - key.root) % 12 in intervals]


def beats_per_bar(time_signature: str) -> float:
    numerator, denominator = map(int, time_signature.split("/"))
    return numerator * (4 / denominator)


def ensure_track(project: Project, name: str, instrument: str) -> Track:
    track_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "track"
    for track in project.tracks:
        if track.id == track_id or track.name.lower() == name.lower():
            return track
    used_channels = {track.channel for track in project.tracks}
    channel = next((value for value in range(16) if value not in used_channels and value != 9), 0)
    track = Track(
        id=track_id,
        name=name.title(),
        instrument=instrument,
        program=PROGRAMS.get(instrument.lower(), 0),
        channel=channel,
    )
    project.tracks.append(track)
    return track


def compose(project: Project, style: str, instruments: list[str], seed: int) -> Project:
    rng = random.Random(seed)
    beats = beats_per_bar(project.time_signature)
    scale = scale_pitches(project.key, 48, 84)
    low_scale = scale_pitches(project.key, 28, 55)
    project.tracks = []

    melody_instrument = instruments[0] if instruments else "piano"
    melody = ensure_track(project, "melody", melody_instrument)
    melody.notes = []

    rhythm_by_style = {
        "ambient": [2.0, 1.0, 1.0],
        "classical": [1.0, 0.5, 0.5, 1.0, 1.0],
        "pop": [0.5, 0.5, 1.0, 0.5, 0.5, 1.0],
        "minimal": [1.0, 1.0, 1.0, 1.0],
    }
    rhythm = rhythm_by_style.get(style, rhythm_by_style["minimal"])
    current_index = scale.index(min(scale, key=lambda pitch: abs(pitch - 67)))

    for bar in range(project.bars):
        cursor = bar * beats
        remaining = beats
        step = 0
        while remaining > 1e-6:
            duration = min(rhythm[step % len(rhythm)], remaining)
            movement = rng.choices([-2, -1, 0, 1, 2, 3], weights=[1, 3, 2, 3, 1, 1])[0]
            current_index = max(0, min(len(scale) - 1, current_index + movement))
            velocity = 82 + rng.randrange(0, 28)
            melody.notes.append(
                Note(
                    pitch=scale[current_index],
                    start=cursor,
                    duration=duration * (0.92 if style != "ambient" else 0.98),
                    velocity=velocity,
                )
            )
            cursor += duration
            remaining -= duration
            step += 1

    if len(instruments) > 1:
        harmony = ensure_track(project, "harmony", instruments[1])
        harmony.notes = []
        key = parse_key(project.key)
        intervals = SCALES[key.mode]
        for bar in range(project.bars):
            degree = [0, 3, 4, 5][bar % 4]
            root_pc = (key.root + intervals[degree]) % 12
            root = next(p for p in range(48, 61) if p % 12 == root_pc)
            third = root + (3 if degree in {1, 2, 5, 6} else 4)
            fifth = root + 7
            for pitch in (root, third, fifth):
                harmony.notes.append(
                    Note(pitch=pitch, start=bar * beats, duration=beats * 0.95, velocity=64)
                )

    if len(instruments) > 2:
        bass = ensure_track(project, "bass", instruments[2])
        bass.notes = []
        key = parse_key(project.key)
        intervals = SCALES[key.mode]
        progression = [0, 5, 3, 4]
        for bar in range(project.bars):
            degree = progression[bar % len(progression)]
            root_pc = (key.root + intervals[degree]) % 12
            pitch = next(p for p in low_scale if p % 12 == root_pc)
            bass.notes.append(Note(pitch=pitch, start=bar * beats, duration=beats * 0.9, velocity=76))

    return project


def harmonize(
    project: Project,
    source_track: str = "melody",
    target_track: str = "harmony",
    instrument: str = "strings",
) -> Project:
    source = next(
        (
            track
            for track in project.tracks
            if track.id == source_track or track.name.lower() == source_track.lower()
        ),
        None,
    )
    if source is None:
        raise ValueError(f"source track not found: {source_track}")
    target = ensure_track(project, target_track, instrument)
    target.instrument = instrument
    target.program = PROGRAMS.get(instrument.lower(), target.program)
    target.notes = []
    scale = scale_pitches(project.key, 36, 96)
    for note in source.notes:
        lower = [pitch for pitch in scale if pitch < note.pitch]
        harmony_pitch = lower[-2] if len(lower) >= 2 else max(0, note.pitch - 3)
        target.notes.append(
            Note(
                pitch=harmony_pitch,
                start=note.start,
                duration=note.duration,
                velocity=max(40, note.velocity - 18),
            )
        )
    return project
