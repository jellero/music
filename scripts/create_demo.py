from __future__ import annotations

from music_studio.service import MusicStudioService


def main() -> None:
    service = MusicStudioService.from_root("data")
    project = service.create_project("Codex Nocturne", tempo=82, key="D minor", bars=8)
    service.compose_project(
        project.id,
        style="classical",
        instruments=["piano", "strings", "bass"],
        seed=42,
    )
    manifest = service.render(project.id)
    print(f"Creato: {project.id}")
    for artifact in manifest["artifacts"]:
        print(f"- {artifact['filename']} ({artifact['size']} byte)")


if __name__ == "__main__":
    main()
