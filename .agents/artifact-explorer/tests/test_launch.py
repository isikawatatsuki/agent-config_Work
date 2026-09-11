import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import launch


class LaunchTests(unittest.TestCase):
    def test_environment_paths(self):
        directory = Path("sample")
        self.assertEqual(launch.environment_python(directory, "posix"), directory / ".venv/bin/python")
        self.assertEqual(launch.environment_python(directory, "nt"), directory / ".venv/Scripts/python.exe")

    def test_missing_environment_does_not_install_or_execute(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(sys, "argv", ["launch.py"]), patch("launch.environment_python", return_value=Path(temporary) / "absent"), patch("launch.subprocess.run") as run, patch("launch.os.execv") as execute:
                self.assertEqual(launch.main(), 1)
                run.assert_not_called()
                execute.assert_not_called()

    def test_launch_uses_venv_without_shell_and_reuses_existing(self):
        with patch.object(sys, "argv", ["launch.py"]), patch("launch.environment_python", return_value=Path(sys.executable)), patch("launch.subprocess.run") as run, patch("launch.os.execv") as execute:
            run.return_value.returncode = 0
            self.assertEqual(launch.main(), 0)
            self.assertEqual(run.call_args.kwargs["timeout"], 15)
            self.assertNotIn("shell", run.call_args.kwargs)
            command = execute.call_args.args[1]
            self.assertIn("--reuse-existing", command)
            self.assertEqual(command[-2:], ["--port", "8765"])

    def test_missing_dependency_does_not_start_server(self):
        with patch.object(sys, "argv", ["launch.py"]), patch("launch.environment_python", return_value=Path(sys.executable)), patch("launch.subprocess.run") as run, patch("launch.os.execv") as execute:
            run.return_value.returncode = 1
            self.assertEqual(launch.main(), 1)
            execute.assert_not_called()

    def test_workspace_task_configuration(self):
        workspace = Path(__file__).parents[3]
        task = json.loads((workspace / ".vscode/tasks.json").read_text())["tasks"][0]
        self.assertEqual(task["type"], "process")
        self.assertEqual(task["runOptions"], {"runOn": "folderOpen", "instanceLimit": 1})
        self.assertEqual(task["windows"]["command"], "py")
        settings = json.loads((workspace / ".vscode/settings.json").read_text())
        self.assertEqual(settings["remote.portsAttributes"]["8765"]["onAutoForward"], "silent")


if __name__ == "__main__":
    unittest.main()