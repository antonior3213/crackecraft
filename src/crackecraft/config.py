from __future__ import annotations

from PySide6.QtCore import QSettings, QStandardPaths


class Settings:
    def __init__(self) -> None:
        self._settings = QSettings("CrackeCraft", "APKLauncher")
        self._settings.setFallbacksEnabled(False)

    @property
    def backend(self) -> str:
        return str(self._settings.value("android/backend", "auto", str))

    @backend.setter
    def backend(self, value: str) -> None:
        self._settings.setValue("android/backend", value)

    @property
    def adb_path(self) -> str:
        return str(self._settings.value("android/adb_path", "", str)).strip()

    @adb_path.setter
    def adb_path(self, value: str) -> None:
        self._settings.setValue("android/adb_path", value.strip())

    @property
    def package_id(self) -> str:
        return str(self._settings.value("android/package_id", "com.mojang.minecraftpe", str)).strip()

    @package_id.setter
    def package_id(self, value: str) -> None:
        self._settings.setValue("android/package_id", value.strip())

    @staticmethod
    def app_data_dir():
        from pathlib import Path

        directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        directory.mkdir(parents=True, exist_ok=True)
        return directory
