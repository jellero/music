from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Note(BaseModel):
    pitch: int = Field(ge=0, le=127)
    start: float = Field(ge=0)
    duration: float = Field(gt=0, le=64)
    velocity: int = Field(default=96, ge=1, le=127)


class Track(BaseModel):
    id: str
    name: str
    instrument: str = "piano"
    program: int = Field(default=0, ge=0, le=127)
    channel: int = Field(default=0, ge=0, le=15)
    volume: float = Field(default=0.8, ge=0, le=1)
    pan: float = Field(default=0.0, ge=-1, le=1)
    notes: list[Note] = Field(default_factory=list)


class Project(BaseModel):
    id: str
    name: str
    tempo: int = Field(default=100, ge=30, le=300)
    key: str = "C major"
    time_signature: str = "4/4"
    bars: int = Field(default=8, ge=1, le=256)
    sample_rate: int = Field(default=44_100, ge=8_000, le=96_000)
    tracks: list[Track] = Field(default_factory=list)
    created_at: str
    updated_at: str

    @field_validator("time_signature")
    @classmethod
    def valid_time_signature(cls, value: str) -> str:
        parts = value.split("/")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("time_signature must look like 4/4")
        numerator, denominator = map(int, parts)
        if numerator < 1 or denominator not in {1, 2, 4, 8, 16}:
            raise ValueError("unsupported time signature")
        return value


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    tempo: int = Field(default=100, ge=30, le=300)
    key: str = "C major"
    time_signature: str = "4/4"
    bars: int = Field(default=8, ge=1, le=256)


class ComposeRequest(BaseModel):
    bars: int | None = Field(default=None, ge=1, le=256)
    style: Literal["ambient", "classical", "pop", "minimal"] = "minimal"
    instruments: list[str] = Field(default_factory=lambda: ["piano", "strings", "bass"])
    seed: int = 7


class AddNoteRequest(BaseModel):
    track: str
    pitch: int = Field(ge=0, le=127)
    start: float = Field(ge=0)
    duration: float = Field(gt=0, le=64)
    velocity: int = Field(default=96, ge=1, le=127)


class ReplaceMeasureRequest(BaseModel):
    track: str
    notes: list[Note]


class HarmonizeRequest(BaseModel):
    source_track: str = "melody"
    target_track: str = "harmony"
    instrument: str = "strings"


class RenderRequest(BaseModel):
    formats: list[Literal["wav", "mid", "musicxml"]] = Field(
        default_factory=lambda: ["wav", "mid", "musicxml"]
    )
