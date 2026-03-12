import asyncio
import subprocess

from enum import Enum
from pathlib import Path

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from .core import (
    ClientFactory,
    ExternalScenario,
    ScenarioConfig,
)

class SDKType(Enum, str):
    PYTHON = "python"
    JS = "js"
    NET = "net"

class SourceScenario(ExternalScenario):
    """Base class for script-based test scenarios."""

    def __init__(
        self,
        script_path: str,
        delay: float = 0.0,
        config: ScenarioConfig | None = None
    ) -> None:
        super().__init__(config)
        self._script_path = Path(script_path)
        self._delay = delay

    @asynccontextmanager
    async def _run_script(self) -> AsyncIterator[None]:



        script_name = self._script_path.name
        script_parent = self._script_path.parent

        proc = subprocess.Popen(
            [f"./{script_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_parent
        )

        # wait for the agent to start running
        await asyncio.sleep(self._delay)

        yield

        proc.terminate()

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start callback server and yield a client factory."""
        async with self._run_script():
            yield super().run()