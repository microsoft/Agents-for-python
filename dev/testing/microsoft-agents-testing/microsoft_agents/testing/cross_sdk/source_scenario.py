# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import shutil
import subprocess
import sys

from pathlib import Path

import psutil

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from microsoft_agents.testing import (
    ActivityTemplate,
    ClientConfig,
    ExternalScenario,
    ScenarioConfig,
)
from microsoft_agents.testing.core import ClientFactory

from .constants import DEFAULT_LOCAL_AGENT_ENDPOINT

_TEMPLATE = {
    "channel_id": "webchat",
    "locale": "en-US",
    "conversation": {"id": "conv1"},
    "from": {"id": "user1", "name": "User"},
    "recipient": {"id": "bot", "name": "Bot"},
}

client_config=ClientConfig(
    activity_template=ActivityTemplate(_TEMPLATE)
)


def _terminate_tree(process: subprocess.Popen, timeout: float = 5.0) -> None:
    """Terminate `process` and all of its descendants.

    Why: Popen.terminate() only signals the immediate PID, so child processes
    spawned by the script (e.g. ``python agent.py`` launched from a .ps1)
    become orphans on both Windows and POSIX.
    """
    try:
        parent = psutil.Process(process.pid)
    except psutil.NoSuchProcess:
        return

    descendants = parent.children(recursive=True)
    targets = [*descendants, parent]

    for proc in targets:
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            pass

    _, alive = psutil.wait_procs(targets, timeout=timeout)
    for proc in alive:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass


class SourceScenario(ExternalScenario):
    """Base class for script-based test scenarios."""

    def __init__(
        self,
        script_path: str,
        delay: float = 0.0,
        config: ScenarioConfig | None = None
    ) -> None:
        super().__init__(DEFAULT_LOCAL_AGENT_ENDPOINT, config)
        self._script_path = Path(script_path)
        self._delay = delay

    @asynccontextmanager
    async def _run_script(self) -> AsyncIterator[None]:

        script_path = self._script_path.resolve()

        runner = shutil.which("pwsh") or shutil.which("powershell")
        if runner is None:
            raise FileNotFoundError("Could not find pwsh or powershell in PATH")

        try:
            process = subprocess.Popen(
                [runner, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=script_path.parent,
                # shell=sys.platform == "win32",
            )

            # wait for the agent to start running
            await asyncio.sleep(self._delay)

            if process.poll() is not None:
                stdout, stderr = process.communicate()  # safe — process is already dead
                raise RuntimeError(
                    f"Agent exited with code {process.returncode} during startup.\n"
                    f"stderr: {stderr.decode(errors='replace')}\n"
                    f"stdout: {stdout.decode(errors='replace')}"
                )

            yield
        finally:
            _terminate_tree(process)
            process.wait()
            # Give the OS time to release the listening socket so chained scenarios
            # on the same port don't hit "address already in use".
            await asyncio.sleep(3.0)

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start callback server and yield a client factory."""
        async with self._run_script():
            async with super().run() as factory:
                yield factory