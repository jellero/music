from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    AddNoteRequest,
    ComposeRequest,
    CreateProjectRequest,
    HarmonizeRequest,
    RenderRequest,
    ReplaceMeasureRequest,
)
from .service import MusicStudioService

service = MusicStudioService.from_root(os.environ.get("MUSIC_STUDIO_DATA"))
app = FastAPI(
    title="Codex Music Studio",
    version="0.1.0",
    description="Composition, editing, synthesis, notation, and export API controlled by Codex.",
)


def not_found(error: FileNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=f"project not found: {error.args[0]}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "codex-music-studio"}


@app.get("/api/projects")
def list_projects() -> list[dict]:
    return service.list_projects()


@app.post("/api/projects", status_code=201)
def create_project(request: CreateProjectRequest) -> dict:
    try:
        return service.create_project(**request.model_dump()).model_dump()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict:
    try:
        project = service.get_project(project_id)
        result = project.model_dump()
        result["manifest"] = service.store.read_manifest(project_id)
        return result
    except FileNotFoundError as error:
        raise not_found(error) from error


@app.post("/api/projects/{project_id}/compose")
def compose_project(project_id: str, request: ComposeRequest) -> dict:
    try:
        return service.compose_project(project_id, **request.model_dump()).model_dump()
    except FileNotFoundError as error:
        raise not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/projects/{project_id}/notes")
def add_note(project_id: str, request: AddNoteRequest) -> dict:
    try:
        return service.add_note(project_id, **request.model_dump()).model_dump()
    except FileNotFoundError as error:
        raise not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.put("/api/projects/{project_id}/measures/{measure}")
def replace_measure(project_id: str, measure: int, request: ReplaceMeasureRequest) -> dict:
    try:
        return service.replace_measure(
            project_id,
            measure,
            request.track,
            request.notes,
        ).model_dump()
    except FileNotFoundError as error:
        raise not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/projects/{project_id}/harmonize")
def harmonize_project(project_id: str, request: HarmonizeRequest) -> dict:
    try:
        return service.harmonize_project(project_id, **request.model_dump()).model_dump()
    except FileNotFoundError as error:
        raise not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/projects/{project_id}/render")
def render_project(project_id: str, request: RenderRequest) -> dict:
    try:
        return service.render(project_id, request.formats)
    except FileNotFoundError as error:
        raise not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/api/projects/{project_id}/artifacts/{filename}")
def get_artifact(project_id: str, filename: str) -> FileResponse:
    try:
        path = service.store.artifact_path(project_id, filename)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found; render the project first")
    return FileResponse(path, filename=filename)


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="studio")
