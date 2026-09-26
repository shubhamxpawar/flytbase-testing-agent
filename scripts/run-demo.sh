#!/usr/bin/env bash
# Audience-facing mode: one headed Chromium session at the runner's 250 ms pace.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runner="$project_dir/.venv/bin/agentic-testing"

if [[ ! -x "$runner" ]]; then
  printf 'Missing virtual environment runner: %s\n' "$runner" >&2
  printf "Create it with: python -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'\n" >&2
  exit 1
fi

exec "$runner" run \
  --target "$project_dir/configs/flytbase-cockpit.yaml" \
  --capabilities "$project_dir/configs/capabilities.example.yaml" \
  --out "$project_dir/artifacts" \
  --headed \
  --reuse-session \
  "$@"
