#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . pyinstaller
PYTHONPATH=src .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir --name CrackeCraft --add-data "src/crackecraft/assets:crackecraft/assets" src/crackecraft/__main__.py
echo "Linux bundle: dist/CrackeCraft/CrackeCraft"
