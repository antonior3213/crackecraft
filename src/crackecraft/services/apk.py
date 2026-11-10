from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Callable


Progress = Callable[[str, int, int], None]
PACKAGE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")


class APKService:
    """Install one Android APK through ADB or Waydroid, then launch its package."""

    @staticmethod
    def validate_apk(path: Path) -> None:
        if path.suffix.lower() != ".apk" or not path.is_file():
            raise ValueError("Elige un archivo con extensión .apk.")
        try:
            with zipfile.ZipFile(path) as package:
                if "AndroidManifest.xml" not in package.namelist():
                    raise ValueError("El archivo no contiene AndroidManifest.xml; no parece una APK instalable.")
        except zipfile.BadZipFile as exc:
            raise ValueError("El archivo seleccionado no es una APK válida.") from exc

    @staticmethod
    def validate_package_id(package_id: str) -> str:
        package_id = package_id.strip()
        if not PACKAGE_PATTERN.fullmatch(package_id):
            raise ValueError("El identificador debe tener formato de paquete Android, por ejemplo com.mojang.minecraftpe.")
        return package_id

    @staticmethod
    def find_adb(configured_path: str = "") -> str | None:
        if configured_path:
            configured = Path(configured_path).expanduser()
            if configured.is_file():
                return str(configured)
        for command in ("adb", "adb.exe"):
            found = shutil.which(command)
            if found:
                return found
        roots = [Path.home() / "Android" / "Sdk"]
        for variable in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
            if os.environ.get(variable):
                roots.insert(0, Path(os.environ[variable]).expanduser())
        candidates = [root / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb") for root in roots]
        if os.name == "nt":
            for variable in ("ProgramFiles", "ProgramFiles(x86)"):
                if os.environ.get(variable):
                    base = Path(os.environ[variable])
                    candidates.extend([
                        base / "BlueStacks_nxt" / "HD-Adb.exe",
                        base / "BlueStacks" / "HD-Adb.exe",
                        base / "LDPlayer9" / "adb.exe",
                    ])
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None

    @staticmethod
    def resolve_backend(mode: str) -> str:
        if mode == "waydroid":
            if os.name == "nt":
                raise RuntimeError("Waydroid solo está disponible en Linux.")
            if not shutil.which("waydroid"):
                raise RuntimeError("No se encontró Waydroid. Instálalo e inicializa Android, o selecciona ADB.")
            return "waydroid"
        if mode == "adb":
            return "adb"
        if mode != "auto":
            raise ValueError("Selecciona ADB o Waydroid como destino Android.")
        if os.name != "nt" and shutil.which("waydroid"):
            return "waydroid"
        return "adb"

    @classmethod
    def list_devices(cls, mode: str, adb_path: str = "") -> list[tuple[str, str]]:
        backend = cls.resolve_backend(mode)
        if backend == "waydroid":
            return [("waydroid", "Waydroid · contenedor local")]
        adb = cls.find_adb(adb_path)
        if not adb:
            raise RuntimeError("No se encontró adb. Instala Android SDK Platform-Tools o selecciona adb.exe en Ajustes.")
        result = subprocess.run([adb, "devices", "-l"], capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout).strip() or "ADB no pudo consultar los dispositivos.")
        devices = cls.parse_devices(result.stdout)
        if not devices:
            raise RuntimeError(cls.device_diagnostic(result.stdout))
        return devices

    @staticmethod
    def device_diagnostic(output: str) -> str:
        states = [fields[1] for line in output.splitlines() if len(fields := line.split()) >= 2 and fields[0] != "List"]
        if "unauthorized" in states:
            return "Emulador detectado, pero sin autorización. Desbloquéalo y acepta «Allow USB debugging / Permitir depuración USB»; luego pulsa Buscar de nuevo."
        if "offline" in states:
            return "Emulador detectado, pero está offline. Reinícialo, espera a que Android termine de arrancar y vuelve a buscar."
        if states:
            return f"ADB detectó un dispositivo en estado «{states[0]}», no listo para instalar. Espera a que arranque o reinicia el emulador."
        return "ADB funciona, pero no ve ningún emulador. Inicia uno y activa ADB/depuración en sus ajustes; después pulsa Buscar de nuevo."

    @staticmethod
    def parse_devices(output: str) -> list[tuple[str, str]]:
        devices: list[tuple[str, str]] = []
        for line in output.splitlines():
            fields = line.split()
            if len(fields) < 2 or fields[1] != "device" or fields[0] == "List":
                continue
            serial = fields[0]
            details = " ".join(fields[2:])
            model = next((part.split(":", 1)[1] for part in fields[2:] if part.startswith("model:")), "Android")
            devices.append((serial, f"{model} · {serial}" if details else serial))
        return devices

    @classmethod
    def install_and_launch(cls, apk_path: Path, package_id: str, mode: str, adb_path: str, serial: str, progress: Progress) -> str:
        cls.validate_apk(apk_path)
        package_id = cls.validate_package_id(package_id)
        backend = cls.resolve_backend(mode)
        if backend == "waydroid":
            progress("Instalando APK en Waydroid…", 0, 0)
            cls._run(["waydroid", "app", "install", str(apk_path)], "No se pudo instalar la APK en Waydroid.")
            progress("Abriendo Minecraft en Waydroid…", 0, 0)
            cls._run(["waydroid", "app", "launch", package_id], "La APK se instaló, pero Waydroid no pudo abrir ese paquete.")
            return "APK instalada y abierta en Waydroid."

        adb = cls.find_adb(adb_path)
        if not adb:
            raise RuntimeError("No se encontró adb. Selecciona la ruta a adb.exe en Ajustes.")
        if not serial:
            raise RuntimeError("Selecciona un emulador Android conectado y en estado «device».")
        progress("Instalando APK en el emulador…", 0, 0)
        cls._run([adb, "-s", serial, "install", "-r", str(apk_path)], "No se pudo instalar la APK en el emulador.")
        progress("Abriendo Minecraft en el emulador…", 0, 0)
        result = cls._run([adb, "-s", serial, "shell", "monkey", "-p", package_id, "-c", "android.intent.category.LAUNCHER", "1"], "La APK se instaló, pero no se pudo abrir.")
        if "No activities found" in result or "monkey aborted" in result.lower():
            raise RuntimeError("La APK se instaló, pero no tiene una actividad de inicio. Comprueba el identificador del paquete.")
        return f"APK instalada y abierta en {serial}."

    @staticmethod
    def _run(command: list[str], error_message: str) -> str:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("La operación Android tardó demasiado. Comprueba que el emulador esté iniciado.") from exc
        except OSError as exc:
            raise RuntimeError(f"No se pudo ejecutar la herramienta Android: {exc}") from exc
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode:
            detail = output.strip()[-1600:]
            raise RuntimeError(f"{error_message}\n{detail}" if detail else error_message)
        return output
