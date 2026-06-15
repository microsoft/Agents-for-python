import asyncio
import pathlib
import shutil
import subprocess
import sys
import time
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from microsoft_agents.testing.cross_sdk import (
    SourceScenario,
    constants
)


class TestSourceScenarioInit:
    def test_stores_script_path(self, tmp_path):
        script = tmp_path / "run_agent.ps1"
        scenario = SourceScenario(str(script))
        assert scenario._script_path == pathlib.Path(str(script))

    def test_default_delay_is_zero(self, tmp_path):
        scenario = SourceScenario(str(tmp_path / "run_agent.ps1"))
        assert scenario._delay == 0.0

    def test_custom_delay(self, tmp_path):
        scenario = SourceScenario(str(tmp_path / "run_agent.ps1"), delay=15.0)
        assert scenario._delay == 15.0

    def test_uses_default_endpoint(self, tmp_path):
        scenario = SourceScenario(str(tmp_path / "run_agent.ps1"))
        # ExternalScenario stores the endpoint; access via the attribute set by super().__init__
        assert scenario._endpoint == constants.DEFAULT_LOCAL_AGENT_ENDPOINT

    def test_accepts_none_config(self, tmp_path):
        scenario = SourceScenario(str(tmp_path / "run_agent.ps1"), config=None)
        assert scenario is not None


def _stub_process() -> MagicMock:
    """MagicMock standing in for a Popen with the attributes _run_script reads."""
    proc = MagicMock()
    proc.poll.return_value = None  # alive — skip the "exited during startup" branch
    return proc


class TestRunScriptPwshDetection:
    async def test_raises_when_no_powershell_found(self, tmp_path):
        script = tmp_path / "run_agent.ps1"
        script.write_text("# stub")
        scenario = SourceScenario(str(script))

        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError, match="pwsh"):
                async with scenario._run_script():
                    pass

    async def test_prefers_pwsh_over_powershell(self, tmp_path):
        script = tmp_path / "run_agent.ps1"
        script.write_text("# stub")
        scenario = SourceScenario(str(script))

        captured = {}

        def _fake_which(name):
            if name == "pwsh":
                return "/usr/bin/pwsh"
            return None

        mock_process = _stub_process()

        with patch("shutil.which", side_effect=_fake_which), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                captured["cmd"] = mock_popen.call_args[0][0]

        assert captured["cmd"][0] == "/usr/bin/pwsh"

    async def test_falls_back_to_powershell(self, tmp_path):
        script = tmp_path / "run_agent.ps1"
        script.write_text("# stub")
        scenario = SourceScenario(str(script))

        captured = {}

        def _fake_which(name):
            if name == "powershell":
                return "C:\\Windows\\powershell.exe"
            return None

        mock_process = _stub_process()

        with patch("shutil.which", side_effect=_fake_which), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                captured["cmd"] = mock_popen.call_args[0][0]

        assert captured["cmd"][0] == "C:\\Windows\\powershell.exe"

    async def test_script_cwd_is_parent_directory(self, tmp_path):
        agent_dir = tmp_path / "my_agent"
        agent_dir.mkdir()
        script = agent_dir / "run_agent.ps1"
        script.write_text("# stub")
        scenario = SourceScenario(str(script))

        mock_process = _stub_process()

        with patch("shutil.which", return_value="/usr/bin/pwsh"), \
             patch("subprocess.Popen", return_value=mock_process) as mock_popen, \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario.asyncio.sleep",
                 new_callable=AsyncMock,
             ), \
             patch(
                 "microsoft_agents.testing.cross_sdk.source_scenario._terminate_tree"
             ):
            async with scenario._run_script():
                pass

        _, kwargs = mock_popen.call_args
        assert kwargs["cwd"] == script.resolve().parent


@pytest.mark.slow
class TestSourceScenarioLifecycle:
    """Verify the subprocess lifecycle: scripts run until the context manager exits."""

    async def test_two_scenarios_sequentially_stop_on_context_exit(self, tmp_path):
        # Need a real PowerShell to actually spawn a long-running process.
        if not (shutil.which("pwsh") or shutil.which("powershell")):
            pytest.skip("pwsh/powershell not available on PATH")

        # Script never exits on its own — the only way it stops is via terminate().
        script = tmp_path / "run_forever.ps1"
        script.write_text("while ($true) { Start-Sleep -Seconds 1 }\n")

        captured: list[subprocess.Popen] = []
        real_popen = subprocess.Popen

        def _capture_popen(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            captured.append(proc)
            return proc

        with patch(
            "microsoft_agents.testing.cross_sdk.source_scenario.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            for run_index in range(2):
                scenario = SourceScenario(str(script))

                async with scenario._run_script():
                    # Process must be alive inside the context.
                    assert captured[-1].poll() is None, (
                        f"Scenario {run_index} exited before the context began"
                    )
                    await asyncio.sleep(5)
                    # Still alive right before the context exits — proves "indefinitely".
                    assert captured[-1].poll() is None, (
                        f"Scenario {run_index} exited on its own during the 5s window"
                    )

                # External check: leaving the context must have shut the process down.
                # Allow a brief grace window in case terminate/wait hasn't fully reaped yet.
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and captured[-1].poll() is None:
                    await asyncio.sleep(0.05)
                assert captured[-1].poll() is not None, (
                    f"Scenario {run_index} subprocess still running after context exit"
                )

        assert len(captured) == 2, "Expected exactly two scripts to be launched"

    async def test_child_process_is_killed_when_context_exits(self, tmp_path):
        """Reproducer for orphaned-child bug.

        A real run_agent.ps1 launches a child (e.g. ``python agent.py``).
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

        script = tmp_path / "run_agent.ps1"
        # & invokes a native command in pwsh; quoted paths handle spaces.
        script.write_text(f'& "{sys.executable}" "{child}"\n')

        captured: list[subprocess.Popen] = []
        real_popen = subprocess.Popen

        def _capture_popen(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            captured.append(proc)
            return proc

        try:
            with patch(
                "microsoft_agents.testing.cross_sdk.source_scenario.subprocess.Popen",
                side_effect=_capture_popen,
            ):
                scenario = SourceScenario(str(script))
                async with scenario._run_script():
                    # Wait for the child to come up and start heartbeating.
                    deadline = time.monotonic() + 5.0
                    while time.monotonic() < deadline and not heartbeat.exists():
                        await asyncio.sleep(0.1)
                    assert heartbeat.exists(), "Child never started heartbeating"
                    await asyncio.sleep(1.0)

                # Let any in-flight terminate() complete, then snapshot mtime
                # and watch for further updates.
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
            # Defensive cleanup so a failed test doesn't leak the orphan.
            if sys.platform == "win32":
                for proc in captured:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
