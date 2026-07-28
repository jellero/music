#!/usr/bin/env sh
set -eu
exec music-studio start --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
