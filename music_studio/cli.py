from __future__ import annotations

import argparse
import json
import os
from typing import Any

import uvicorn

from .models import Note
from .service import MusicStudioService


def emit(value: Any) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    print(json.dumps(value, indent=2, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="music-studio")
    root.add_argument("--data", default=os.environ.get("MUSIC_STUDIO_DATA", "data"))
    commands = root.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start", help="Start the web studio and REST API")
    start.add_argument("--host", default="0.0.0.0")
    start.add_argument("--port", type=int, default=8000)
    start.add_argument("--reload", action="store_true")

    commands.add_parser("list", help="List projects")

    create = commands.add_parser("create", help="Create a project")
    create.add_argument("name")
    create.add_argument("--tempo", type=int, default=100)
    create.add_argument("--key", default="C major")
    create.add_argument("--time-signature", default="4/4")
    create.add_argument("--bars", type=int, default=8)

    show = commands.add_parser("show", help="Show a project")
    show.add_argument("project_id")

    compose = commands.add_parser("compose", help="Compose a project")
    compose.add_argument("project_id")
    compose.add_argument("--style", default="minimal")
    compose.add_argument("--instruments", default="piano,strings,bass")
    compose.add_argument("--bars", type=int)
    compose.add_argument("--seed", type=int, default=7)

    add = commands.add_parser("add-note", help="Add a note")
    add.add_argument("project_id")
    add.add_argument("track")
    add.add_argument("pitch", type=int)
    add.add_argument("start", type=float)
    add.add_argument("duration", type=float)
    add.add_argument("--velocity", type=int, default=96)
    add.add_argument("--instrument", default="piano")

    replace = commands.add_parser("replace-measure", help="Replace a measure from JSON")
    replace.add_argument("project_id")
    replace.add_argument("measure", type=int)
    replace.add_argument("track")
    replace.add_argument("notes_json")
    replace.add_argument("--instrument", default="piano")

    harmony = commands.add_parser("harmonize", help="Harmonize a track")
    harmony.add_argument("project_id")
    harmony.add_argument("--source", default="melody")
    harmony.add_argument("--target", default="harmony")
    harmony.add_argument("--instrument", default="strings")

    render = commands.add_parser("render", help="Render artifacts")
    render.add_argument("project_id")
    render.add_argument("--formats", default="wav,mid,musicxml")
    return root


def main() -> None:
    args = parser().parse_args()
    os.environ["MUSIC_STUDIO_DATA"] = args.data
    if args.command == "start":
        uvicorn.run(
            "music_studio.api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return

    service = MusicStudioService.from_root(args.data)
    if args.command == "list":
        emit(service.list_projects())
    elif args.command == "create":
        emit(service.create_project(args.name, args.tempo, args.key, args.time_signature, args.bars))
    elif args.command == "show":
        emit(service.get_project(args.project_id))
    elif args.command == "compose":
        emit(
            service.compose_project(
                args.project_id,
                args.style,
                [value.strip() for value in args.instruments.split(",") if value.strip()],
                args.bars,
                args.seed,
            )
        )
    elif args.command == "add-note":
        emit(
            service.add_note(
                args.project_id,
                args.track,
                args.pitch,
                args.start,
                args.duration,
                args.velocity,
                args.instrument,
            )
        )
    elif args.command == "replace-measure":
        notes = [Note.model_validate(item) for item in json.loads(args.notes_json)]
        emit(service.replace_measure(args.project_id, args.measure, args.track, notes, args.instrument))
    elif args.command == "harmonize":
        emit(service.harmonize_project(args.project_id, args.source, args.target, args.instrument))
    elif args.command == "render":
        emit(service.render(args.project_id, [value.strip() for value in args.formats.split(",")]))


if __name__ == "__main__":
    main()
