import asyncio
import pathlib
import shutil
import subprocess
import sys
import time
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from microsoft_agents.testing import SourceScenario
import microsoft_agents.testing.constants as constants


class TestSourceScenarioInit:
    def test_stores_agent_path_and_script(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")
        assert scenario._agent_path == pathlib.Path(str(tmp_path))
        assert scenario._script == "python agent.py"

    def test_default_delay_is_zero(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")
        assert scenario._delay == 0.0

    def test_custom_delay(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py", delay=15.0)
        assert scenario._delay == 15.0

    def test_uses_default_endpoint(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")
        assert scenario._endpoint == constants.DEFAULT_LOCAL_AGENT_ENDPOINT

    def test_accepts_none_config(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py", config=None)
        assert scenario is not None


def _stub_process() -> MagicMock:
    """MagicMock standing in for a Popen with the attributes _run_script reads."""
    proc = MagicMock()
    proc.poll.return_value = None  # alive — skip the "exited during startup" branch
    return proc


class TestRunScriptPwshDetection:
    async def test_raises_when_no_powershell_found(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")

        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError, match="pwsh"):
                async with scenario._run_script():
                    pass

    async def test_prefers_pwsh_over_powershell(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")

        captured = {}

        def _fake_which(name):
            if name == "pwsh":
                return "/usr/bin/pwsh"
            return None

        mock_process = _stub_process()

        with patch("shutil.which", side_effect=_fake_which), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                captured["cmd"] = mock_popen.call_args[0][0]

        assert captured["cmd"][0] == "/usr/bin/pwsh"

    async def test_falls_back_to_powershell(self, tmp_path):
        scenario = SourceScenario(str(tmp_path), "python agent.py")

        captured = {}

        def _fake_which(name):
            if name == "powershell":
                return "C:\\Windows\\powershell.exe"
            return None

        mock_process = _stub_process()

        with patch("shutil.which", side_effect=_fake_which), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                captured["cmd"] = mock_popen.call_args[0][0]

        assert captured["cmd"][0] == "C:\\Windows\\powershell.exe"

    async def test_script_cwd_is_agent_path(self, tmp_path):
        agent_dir = tmp_path / "my_agent"
        agent_dir.mkdir()
        scenario = SourceScenario(str(agent_dir), "python agent.py")

        mock_process = _stub_process()

        with patch("shutil.which", return_value="/usr/bin/pwsh"), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                pass

        _, kwargs = mock_popen.call_args
        assert kwargs["cwd"] == agent_dir.resolve()


@pytest.mark.slow
class TestSourceScenarioLifecycle:
    """Verify the subprocess lifecycle: scripts run until the context manager exits."""

    async def test_two_scenarios_sequentially_stop_on_context_exit(self, tmp_path):
        # Need a real PowerShell to actually spawn a long-running process.
        if not (shutil.which("pwsh") or shutil.which("powershell")):
            pytest.skip("pwsh/powershell not available on PATH")

        captured: list[subprocess.Popen] = []
        real_popen = subprocess.Popen

        def _capture_popen(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            captured.append(proc)
            return proc

        with patch(
            "microsoft_agents.testing.source_scenario.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            for run_index in range(2):
                scenario = SourceScenario(
                    str(tmp_path),
                    "while ($true) { Start-Sleep -Seconds 1 }",
                )

                async with scenario._run_script():
                    assert captured[-1].poll() is None, (
                        f"Scenario {run_index} exited before the context began"
                    )
                    await asyncio.sleep(5)
                    assert captured[-1].poll() is None, (
                        f"Scenario {run_index} exited on its own during the 5s window"
                    )

                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and captured[-1].poll() is None:
                    await asyncio.sleep(0.05)
                assert captured[-1].poll() is not None, (
                    f"Scenario {run_index} subprocess still running after context exit"
                )

        assert len(captured) == 2, "Expected exactly two scripts to be launched"

    async def test_child_process_is_killed_when_context_exits(self, tmp_path):
        """Reproducer for orphaned-child bug.

        A real script launches a child (e.g. ``python agent.py``).
        terminate() on the pwsh PID does NOT kill its descendants on Windows
        or POSIX, so the child becomes an orphan. We detect this by watching
        a heartbeat file the child writes every 0.2s — if its mtime keeps
        advancing after the context exits, the child is still alive.
        """
        if not (shutil.which("pwsh") or shutil.which("powershell")):
            pytest.skip("pwsh/powershell not available on PATH")

        heartbeat = tmp_path / "heartbeat.txt"
        child = tmp_path / "child.py"
        child.write_text(
            "import time\n"
            "while True:\n"
            f"    open(r'{heartbeat}', 'w').write(str(time.time()))\n"
            "    time.sleep(0.2)\n"
        )

        ps_command = f'& "{sys.executable}" "{child}"'

        captured: list[subprocess.Popen] = []
        real_popen = subprocess.Popen

        def _capture_popen(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            captured.append(proc)
            return proc

        try:
            with patch(
                "microsoft_agents.testing.source_scenario.subprocess.Popen",
                side_effect=_capture_popen,
            ):
                scenario = SourceScenario(str(tmp_path), ps_command)
                async with scenario._run_script():
                    deadline = time.monotonic() + 5.0
                    while time.monotonic() < deadline and not heartbeat.exists():
                        await asyncio.sleep(0.1)
                    assert heartbeat.exists(), "Child never started heartbeating"
                    await asyncio.sleep(1.0)

                await asyncio.sleep(1.0)
                mtime_after_exit = heartbeat.stat().st_mtime
                await asyncio.sleep(2.0)
                final_mtime = heartbeat.stat().st_mtime

                assert final_mtime == mtime_after_exit, (
                    "Heartbeat file is still being updated after context exit — "
                    "child process is orphaned. terminate() killed the pwsh "
                    "wrapper but not its descendants."
                )
        finally:
            if sys.platform == "win32":
                for proc in captured:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
