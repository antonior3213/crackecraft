$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\python.exe -m pip install -e . pyinstaller
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name CrackeCraft --hidden-import win32ctypes.pywin32.win32cred --hidden-import win32ctypes.pywin32.pywintypes --hidden-import win32ctypes.pywin32.win32api --collect-submodules win32ctypes.core.ctypes --add-data "src\crackecraft\assets;crackecraft\assets" src\crackecraft\__main__.py
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($iscc) {
    & $iscc.Source (Join-Path $PSScriptRoot "installer.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup no pudo crear el instalador." }
    Write-Host "Bundle e instalador creados en dist\CrackeCraft y dist\installer."
} else {
    Write-Host "Bundle compilado en dist\CrackeCraft. Instala Inno Setup 6 y compila installer.iss para obtener Setup.exe."
}
