#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
else
  echo "Virtual environment not found. Create .venv or venv first." >&2
  exit 1
fi

required_files=(
  "$ROOT_DIR/data/prompts.md"
  "$ROOT_DIR/data/resume_master.md"
  "$ROOT_DIR/data/keywords.txt"
)

for required_file in "${required_files[@]}"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Required file not found: $required_file" >&2
    exit 1
  fi
done

exec "$PYTHON_BIN" "$ROOT_DIR/main.py" "$@"
