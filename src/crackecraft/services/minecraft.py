from __future__ import annotations

import shlex
from pathlib import Path
from typing import Callable

import minecraft_launcher_lib
from minecraft_launcher_lib.types import MinecraftOptions


Progress = Callable[[str, int, int], None]


class MinecraftService:
    @staticmethod
    def versions() -> list[dict]:
        return [dict(version) for version in minecraft_launcher_lib.utils.get_version_list()]

    @staticmethod
    def installed_versions(game_dir: Path) -> list[dict]:
        try:
            return [dict(version) for version in minecraft_launcher_lib.utils.get_installed_versions(str(game_dir))]
        except OSError:
            return []

    @staticmethod
    def install(version: str, game_dir: Path, progress: Progress) -> None:
        game_dir.mkdir(parents=True, exist_ok=True)
        status_value = "Preparando descarga"
        current_progress = 0
        maximum = 0

        def set_status(status: str) -> None:
            nonlocal status_value
            status_value = status
            progress(status_value, current_progress, maximum)

        def set_progress(value: int) -> None:
            nonlocal current_progress
            current_progress = value
            progress(status_value, current_progress, maximum)

        def set_maximum(value: int) -> None:
            nonlocal maximum
            maximum = value
            progress(status_value, current_progress, maximum)

        minecraft_launcher_lib.install.install_minecraft_version(version, str(game_dir), {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_maximum,
        })

    @staticmethod
    def launch_command(version: str, root: Path, game_dir: Path, account: dict[str, str], memory_mb: int, java_path: str, extra_args: str) -> list[str]:
        if not account.get("access_token"):
            raise ValueError("La sesión no tiene un token de Minecraft válido.")
        options: MinecraftOptions = {
            "username": account["name"],
            "uuid": account["id"],
            "token": account["access_token"],
            "launcherName": "CrackeCraft",
            "launcherVersion": "0.1.0",
            "gameDirectory": str(game_dir),
            "jvmArguments": [f"-Xmx{memory_mb}M", *shlex.split(extra_args)],
        }
        if java_path:
            options["executablePath"] = java_path
        return minecraft_launcher_lib.command.get_minecraft_command(version, str(root), options)

    @staticmethod
    def remove_version(version: str, game_dir: Path) -> None:
        target = (game_dir / "versions" / version).resolve()
        versions_root = (game_dir / "versions").resolve()
        if target.parent != versions_root or not target.exists():
            raise ValueError("La carpeta de versión no existe o su ruta no es segura.")
        import shutil
        shutil.rmtree(target)

    @staticmethod
    def java_executable() -> str:
        try:
            return minecraft_launcher_lib.utils.get_java_executable()
        except (OSError, RuntimeError, ValueError):
            return "java"

