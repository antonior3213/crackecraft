#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ ! -x .venv/bin/python ]]; then
  echo "No existe .venv. Consulta README.md para instalar CrackeCraft." >&2
  exit 1
fi
PYTHONPATH=src exec .venv/bin/python -m crackecraft "$@"
