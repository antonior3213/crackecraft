@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo No existe el entorno .venv. Consulta README.md para instalar CrackeCraft.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m crackecraft
if errorlevel 1 pause
