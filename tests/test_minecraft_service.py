from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crackecraft.services.minecraft import MinecraftService


class MinecraftServiceTests(unittest.TestCase):
    def test_remove_version_only_removes_version_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            version_dir = root / "versions" / "1.20.4"
            version_dir.mkdir(parents=True)
            (version_dir / "1.20.4.json").write_text("{}", encoding="utf-8")
            MinecraftService.remove_version("1.20.4", root)
            self.assertFalse(version_dir.exists())

    def test_remove_version_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "escape"
            outside.mkdir()
            (root / "versions").mkdir()
            with self.assertRaises(ValueError):
                MinecraftService.remove_version("../escape", root)
            self.assertTrue(outside.exists())

    @patch("crackecraft.services.minecraft.minecraft_launcher_lib.install.install_minecraft_version")
    def test_install_forwards_progress_callbacks(self, install_version) -> None:
        events: list[tuple[str, int, int]] = []
        with tempfile.TemporaryDirectory() as temporary:
            MinecraftService.install("1.20.4", Path(temporary), lambda status, current, maximum: events.append((status, current, maximum)))
        callbacks = install_version.call_args.args[2]
        callbacks["setStatus"]("Downloading assets")
        callbacks["setMax"](4)
        callbacks["setProgress"](2)
        self.assertEqual(events[-1], ("Downloading assets", 2, 4))

    @patch("crackecraft.services.minecraft.minecraft_launcher_lib.command.get_minecraft_command")
    def test_launch_builds_authenticated_vanilla_command(self, command_builder) -> None:
        command_builder.return_value = ["java", "-Xmx2048M", "net.minecraft.client.main.Main"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profiles" / "default"
            account = {"id": "uuid-123", "name": "Player", "access_token": "secret-token"}
            result = MinecraftService().launch_command("1.20.4", root, profile, account, 2048, "", "-Dfoo=bar")
            self.assertEqual(result[0], "java")
            options = command_builder.call_args.args[2]
            self.assertEqual(options["uuid"], "uuid-123")
            self.assertEqual(options["token"], "secret-token")
            self.assertEqual(options["gameDirectory"], str(profile))
            self.assertIn("-Xmx2048M", options["jvmArguments"])
            self.assertIn("-Dfoo=bar", options["jvmArguments"])


if __name__ == "__main__":
    unittest.main()
