#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
model="${1:-}"
case "$model" in
  qwen|hyperclova) ;;
  *) echo 'Usage: bash setup.sh {qwen|hyperclova}' >&2; exit 2 ;;
esac
python3 -m venv ".venv-$model"
".venv-$model/bin/python" -m pip install --upgrade pip
".venv-$model/bin/python" -m pip install -r "requirements-$model.txt"
