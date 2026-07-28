from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Project


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


class ProjectStore:
    def __init__(self, root: str | Path | None = None) -> None:
        configured = root or os.environ.get("MUSIC_STUDIO_DATA", "data")
        self.root = Path(configured).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        safe = slugify(project_id)
        if safe != project_id:
            raise ValueError("invalid project id")
        path = (self.root / safe).resolve()
        if self.root not in path.parents:
            raise ValueError("invalid project path")
        return path

    def project_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def artifact_dir(self, project_id: str) -> Path:
        directory = self._project_dir(project_id) / "artifacts"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def create_id(self, name: str) -> str:
        base = slugify(name)
        candidate = base
        counter = 2
        while self.project_path(candidate).exists():
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    def save(self, project: Project) -> Project:
        project.updated_at = utc_now()
        directory = self._project_dir(project.id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "project.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(target)
        return project

    def load(self, project_id: str) -> Project:
        target = self.project_path(project_id)
        if not target.exists():
            raise FileNotFoundError(project_id)
        return Project.model_validate_json(target.read_text(encoding="utf-8"))

    def list(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*/project.json")):
            try:
                project = Project.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            projects.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "tempo": project.tempo,
                    "key": project.key,
                    "bars": project.bars,
                    "tracks": len(project.tracks),
                    "updated_at": project.updated_at,
                }
            )
        return sorted(projects, key=lambda item: item["updated_at"], reverse=True)

    def artifact_path(self, project_id: str, filename: str) -> Path:
        if Path(filename).name != filename:
            raise ValueError("invalid artifact filename")
        path = (self.artifact_dir(project_id) / filename).resolve()
        if self.artifact_dir(project_id) not in path.parents:
            raise ValueError("invalid artifact path")
        return path

    def read_manifest(self, project_id: str) -> dict[str, Any]:
        path = self.artifact_dir(project_id) / "manifest.json"
        if not path.exists():
            return {"project_id": project_id, "artifacts": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_manifest(self, project_id: str, data: dict[str, Any]) -> None:
        path = self.artifact_dir(project_id) / "manifest.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
