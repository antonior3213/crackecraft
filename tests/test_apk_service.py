from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from crackecraft.services.apk import APKService


class APKServiceTests(unittest.TestCase):
    def test_parse_devices_keeps_only_authorized_connected_targets(self) -> None:
        output = """List of devices attached
emulator-5554 device product:sdk_gphone64_x86_64 model:Pixel_8
192.168.1.10:5555 unauthorized transport_id:3
offline-1 offline
"""
        self.assertEqual(
            APKService.parse_devices(output),
            [("emulator-5554", "Pixel_8 · emulator-5554")],
        )

    def test_package_id_rejects_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            APKService.validate_package_id("com.mojang; start bad-command")

    def test_validate_apk_requires_android_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "not-an-apk.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("readme.txt", "no manifest")
            with self.assertRaisesRegex(ValueError, "AndroidManifest.xml"):
                APKService.validate_apk(apk)

    @patch.object(APKService, "_run", side_effect=["Success", "Events injected: 1"])
    @patch.object(APKService, "find_adb", return_value="adb.exe")
    def test_adb_install_and_launch_use_argument_lists(self, find_adb, run):
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "minecraft.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("AndroidManifest.xml", b"manifest")
            progress: list[str] = []
            result = APKService.install_and_launch(apk, "com.mojang.minecraftpe", "adb", "", "emulator-5554", lambda status, _value, _maximum: progress.append(status))
        self.assertEqual(result, "APK instalada y abierta en emulator-5554.")
        self.assertEqual(run.call_args_list[0].args[0], ["adb.exe", "-s", "emulator-5554", "install", "-r", str(apk)])
        self.assertEqual(run.call_args_list[1].args[0][:4], ["adb.exe", "-s", "emulator-5554", "shell"])
        self.assertIn("Instalando APK en el emulador…", progress)
        self.assertIn("Abriendo Minecraft en el emulador…", progress)


if __name__ == "__main__":
    unittest.main()
