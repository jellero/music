from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import Note, Project
from .render import render_midi, render_musicxml, render_wav
from .storage import ProjectStore, utc_now
from .theory import PROGRAMS, beats_per_bar, compose, ensure_track, harmonize


@dataclass
class MusicStudioService:
    store: ProjectStore

    @classmethod
    def from_root(cls, root: str | Path | None = None) -> "MusicStudioService":
        return cls(ProjectStore(root))

    def create_project(
        self,
        name: str,
        tempo: int = 100,
        key: str = "C major",
        time_signature: str = "4/4",
        bars: int = 8,
    ) -> Project:
        project_id = self.store.create_id(name)
        now = utc_now()
        project = Project(
            id=project_id,
            name=name.strip(),
            tempo=tempo,
            key=key,
            time_signature=time_signature,
            bars=bars,
            created_at=now,
            updated_at=now,
        )
        return self.store.save(project)

    def list_projects(self) -> list[dict]:
        return self.store.list()

    def get_project(self, project_id: str) -> Project:
        return self.store.load(project_id)

    def compose_project(
        self,
        project_id: str,
        style: str = "minimal",
        instruments: list[str] | None = None,
        bars: int | None = None,
        seed: int = 7,
    ) -> Project:
        project = self.get_project(project_id)
        if bars is not None:
            project.bars = bars
        compose(project, style, instruments or ["piano", "strings", "bass"], seed)
        return self.store.save(project)

    def add_note(
        self,
        project_id: str,
        track_name: str,
        pitch: int,
        start: float,
        duration: float,
        velocity: int = 96,
        instrument: str = "piano",
    ) -> Project:
        project = self.get_project(project_id)
        track = ensure_track(project, track_name, instrument)
        track.notes.append(Note(pitch=pitch, start=start, duration=duration, velocity=velocity))
        track.notes.sort(key=lambda note: (note.start, note.pitch))
        total_beats = start + duration
        required_bars = max(
            1,
            int((total_beats - 1e-9) // beats_per_bar(project.time_signature)) + 1,
        )
        project.bars = max(project.bars, required_bars)
        return self.store.save(project)

    def replace_measure(
        self,
        project_id: str,
        measure: int,
        track_name: str,
        notes: Iterable[Note],
        instrument: str = "piano",
    ) -> Project:
        if measure < 1:
            raise ValueError("measure is 1-based")
        project = self.get_project(project_id)
        track = ensure_track(project, track_name, instrument)
        beats = beats_per_bar(project.time_signature)
        measure_start = (measure - 1) * beats
        measure_end = measure_start + beats
        track.notes = [
            note for note in track.notes if not (measure_start <= note.start < measure_end)
        ]
        for note in notes:
            if note.start < 0 or note.start >= beats:
                raise ValueError("note.start must be relative to the measure")
            track.notes.append(
                Note(
                    pitch=note.pitch,
                    start=measure_start + note.start,
                    duration=note.duration,
                    velocity=note.velocity,
                )
            )
        track.notes.sort(key=lambda note: (note.start, note.pitch))
        project.bars = max(project.bars, measure)
        return self.store.save(project)

    def harmonize_project(
        self,
        project_id: str,
        source_track: str = "melody",
        target_track: str = "harmony",
        instrument: str = "strings",
    ) -> Project:
        project = self.get_project(project_id)
        harmonize(project, source_track, target_track, instrument)
        return self.store.save(project)

    def set_track_mix(
        self,
        project_id: str,
        track_name: str,
        volume: float | None = None,
        pan: float | None = None,
        instrument: str | None = None,
    ) -> Project:
        project = self.get_project(project_id)
        track = next(
            (
                item
                for item in project.tracks
                if item.id == track_name or item.name.lower() == track_name.lower()
            ),
            None,
        )
        if track is None:
            raise ValueError(f"track not found: {track_name}")
        if volume is not None:
            track.volume = volume
        if pan is not None:
            track.pan = pan
        if instrument is not None:
            track.instrument = instrument
            track.program = PROGRAMS.get(instrument.lower(), track.program)
        return self.store.save(project)

    def render(self, project_id: str, formats: list[str] | None = None) -> dict:
        project = self.get_project(project_id)
        selected = formats or ["wav", "mid", "musicxml"]
        artifact_dir = self.store.artifact_dir(project_id)
        artifacts: list[dict[str, str | int]] = []
        renderers = {
            "wav": (render_wav, f"{project.id}.wav", "audio/wav"),
            "mid": (render_midi, f"{project.id}.mid", "audio/midi"),
            "musicxml": (
                render_musicxml,
                f"{project.id}.musicxml",
                "application/vnd.recordare.musicxml+xml",
            ),
        }
        for fmt in selected:
            if fmt not in renderers:
                raise ValueError(f"unsupported format: {fmt}")
            renderer, filename, media_type = renderers[fmt]
            path = renderer(project, artifact_dir / filename)
            artifacts.append(
                {
                    "format": fmt,
                    "filename": filename,
                    "media_type": media_type,
                    "size": path.stat().st_size,
                    "url": f"/api/projects/{project.id}/artifacts/{filename}",
                }
            )
        manifest = {
            "project_id": project.id,
            "artifacts": artifacts,
            "updated_at": utc_now(),
        }
        self.store.write_manifest(project.id, manifest)
        return manifest
