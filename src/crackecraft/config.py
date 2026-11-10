from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

from PySide6.QtCore import QStandardPaths, QSettings

from crackecraft import __version__


class Settings:
    def __init__(self) -> None:
        self._settings = QSettings("CrackeCraft", "Launcher")
        self._settings.setFallbacksEnabled(False)

    @property
    def client_id(self) -> str:
        return cast(str, self._settings.value("auth/client_id", "", str)).strip()

    @client_id.setter
    def client_id(self, value: str) -> None:
        self._settings.setValue("auth/client_id", value.strip())

    @property
    def game_dir(self) -> Path:
        saved = cast(str, self._settings.value("game/directory", "", str)).strip()
        if saved:
            return Path(saved).expanduser()
        home = Path.home()
        if os.name == "nt":
            return Path(os.environ.get("APPDATA", home)) / ".minecraft"
        if os.uname().sysname == "Darwin":
            return home / "Library" / "Application Support" / "minecraft"
        return home / ".minecraft"

    @game_dir.setter
    def game_dir(self, value: str | Path) -> None:
        self._settings.setValue("game/directory", str(Path(value).expanduser()))

    @property
    def memory_mb(self) -> int:
        return cast(int, self._settings.value("game/memory_mb", 4096))

    @memory_mb.setter
    def memory_mb(self, value: int) -> None:
        self._settings.setValue("game/memory_mb", max(1024, int(value)))

    @property
    def java_path(self) -> str:
        return cast(str, self._settings.value("game/java_path", "", str)).strip()

    @java_path.setter
    def java_path(self, value: str) -> None:
        self._settings.setValue("game/java_path", value.strip())

    @property
    def jvm_args(self) -> str:
        return cast(str, self._settings.value("game/jvm_args", "", str))

    @jvm_args.setter
    def jvm_args(self, value: str) -> None:
        self._settings.setValue("game/jvm_args", value.strip())

    @property
    def selected_profile(self) -> str:
        return cast(str, self._settings.value("profiles/selected", "default", str))

    @selected_profile.setter
    def selected_profile(self, value: str) -> None:
        self._settings.setValue("profiles/selected", value)

    @property
    def active_account(self) -> str:
        return cast(str, self._settings.value("accounts/active", "", str))

    @active_account.setter
    def active_account(self, value: str) -> None:
        self._settings.setValue("accounts/active", value)

    def profiles(self) -> dict[str, dict[str, str]]:
        raw = cast(str, self._settings.value("profiles/data", "{}", str))
        try:
            profiles = json.loads(raw)
            if isinstance(profiles, dict):
                return profiles
        except (ValueError, TypeError):
            pass
        return {}

    def save_profiles(self, profiles: dict[str, dict[str, str]]) -> None:
        self._settings.setValue("profiles/data", json.dumps(profiles, ensure_ascii=False))

    def accounts(self) -> dict[str, dict[str, str]]:
        raw = cast(str, self._settings.value("accounts/data", "{}", str))
        try:
            accounts = json.loads(raw)
            if isinstance(accounts, dict):
                return accounts
        except (ValueError, TypeError):
            pass
        return {}

    def save_accounts(self, accounts: dict[str, dict[str, str]]) -> None:
        self._settings.setValue("accounts/data", json.dumps(accounts, ensure_ascii=False))

    @staticmethod
    def app_data_dir() -> Path:
        path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def launcher_version() -> str:
        return __version__
