from __future__ import annotations

import json
import wave
from pathlib import Path
from xml.etree import ElementTree

from music_studio.models import Note
from music_studio.service import MusicStudioService


def test_complete_music_workflow(tmp_path: Path) -> None:
    service = MusicStudioService.from_root(tmp_path)
    project = service.create_project("Test Suite", tempo=120, key="D minor", bars=2)
    project = service.compose_project(project.id, style="minimal", seed=13)

    assert project.id == "test-suite"
    assert len(project.tracks) == 3
    assert sum(len(track.notes) for track in project.tracks) > 8

    manifest = service.render(project.id)
    assert {item["format"] for item in manifest["artifacts"]} == {"wav", "mid", "musicxml"}

    artifact_dir = tmp_path / project.id / "artifacts"
    wav_path = artifact_dir / f"{project.id}.wav"
    midi_path = artifact_dir / f"{project.id}.mid"
    xml_path = artifact_dir / f"{project.id}.musicxml"

    with wave.open(str(wav_path), "rb") as wav:
        assert wav.getnchannels() == 2
        assert wav.getframerate() == 44_100
        assert wav.getnframes() > 1_000

    assert midi_path.read_bytes().startswith(b"MThd")
    assert ElementTree.parse(xml_path).getroot().tag == "score-partwise"
    assert json.loads((artifact_dir / "manifest.json").read_text())["project_id"] == project.id


def test_edit_and_harmonize(tmp_path: Path) -> None:
    service = MusicStudioService.from_root(tmp_path)
    project = service.create_project("Edit", bars=1)
    service.add_note(project.id, "melody", 60, 0, 1)
    service.replace_measure(
        project.id,
        1,
        "melody",
        [Note(pitch=64, start=0, duration=1), Note(pitch=67, start=1, duration=1)],
    )
    project = service.harmonize_project(project.id)

    melody = next(track for track in project.tracks if track.id == "melody")
    harmony = next(track for track in project.tracks if track.id == "harmony")
    assert [note.pitch for note in melody.notes] == [64, 67]
    assert len(harmony.notes) == len(melody.notes)
    assert all(h.pitch < m.pitch for h, m in zip(harmony.notes, melody.notes, strict=True))
