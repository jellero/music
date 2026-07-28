from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .models import Note
from .service import MusicStudioService

service = MusicStudioService.from_root(os.environ.get("MUSIC_STUDIO_DATA"))
mcp = FastMCP(
    "Codex Music Studio",
    instructions=(
        "Create, compose, edit, harmonize, render, and inspect local music projects. "
        "Use render_project after structural edits so the browser can play the current WAV."
    ),
)


@mcp.tool()
def list_projects() -> list[dict]:
    """List all music projects and their current metadata."""
    return service.list_projects()


@mcp.tool()
def create_project(
    name: str,
    tempo: int = 100,
    key: str = "C major",
    time_signature: str = "4/4",
    bars: int = 8,
) -> dict:
    """Create an empty music project."""
    return service.create_project(name, tempo, key, time_signature, bars).model_dump()


@mcp.tool()
def get_project(project_id: str) -> dict:
    """Read the full editable score model for a project."""
    project = service.get_project(project_id).model_dump()
    project["manifest"] = service.store.read_manifest(project_id)
    return project


@mcp.tool()
def compose_project(
    project_id: str,
    style: str = "minimal",
    instruments: list[str] | None = None,
    bars: int | None = None,
    seed: int = 7,
) -> dict:
    """Generate a deterministic multi-track composition for an existing project."""
    return service.compose_project(
        project_id,
        style=style,
        instruments=instruments,
        bars=bars,
        seed=seed,
    ).model_dump()


@mcp.tool()
def add_note(
    project_id: str,
    track: str,
    pitch: int,
    start: float,
    duration: float,
    velocity: int = 96,
    instrument: str = "piano",
) -> dict:
    """Add one MIDI note to a track. start and duration are measured in quarter-note beats."""
    return service.add_note(
        project_id,
        track,
        pitch,
        start,
        duration,
        velocity,
        instrument,
    ).model_dump()


@mcp.tool()
def replace_measure(
    project_id: str,
    measure: int,
    track: str,
    notes: list[dict],
    instrument: str = "piano",
) -> dict:
    """Replace a 1-based measure on a track; note starts are relative to that measure."""
    parsed = [Note.model_validate(note) for note in notes]
    return service.replace_measure(
        project_id,
        measure,
        track,
        parsed,
        instrument,
    ).model_dump()


@mcp.tool()
def harmonize_project(
    project_id: str,
    source_track: str = "melody",
    target_track: str = "harmony",
    instrument: str = "strings",
) -> dict:
    """Generate a diatonic harmony track from a source track."""
    return service.harmonize_project(
        project_id,
        source_track,
        target_track,
        instrument,
    ).model_dump()


@mcp.tool()
def set_track_mix(
    project_id: str,
    track: str,
    volume: float | None = None,
    pan: float | None = None,
    instrument: str | None = None,
) -> dict:
    """Change a track's volume, stereo pan, or synthesis instrument."""
    return service.set_track_mix(project_id, track, volume, pan, instrument).model_dump()


@mcp.tool()
def render_project(project_id: str, formats: list[str] | None = None) -> dict:
    """Render WAV, MIDI, and MusicXML artifacts for a project."""
    return service.render(project_id, formats)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
