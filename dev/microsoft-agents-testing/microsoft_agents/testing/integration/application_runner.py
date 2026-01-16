# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional
from threading import Thread

from microsoft_agents.hosting.core import AgentApplication


class ApplicationRunner(ABC):
    """Base class for application runners."""

    def __init__(self, app: Any):
        self._app = app
        self._thread: Optional[Thread] = None

    async def start_server(self) -> None:
        pass

    async def close(self) -> None:
        pass

    @abstractmethod
    async def _start_server(self) -> None:
        raise NotImplementedError(
            "Start server method must be implemented by subclasses"
        )

    async def _stop_server(self) -> None:
        pass

    async def __aenter__(self) -> None:

        if self._thread:
            raise RuntimeError("Server is already running")

        def target():
            asyncio.run(self._start_server())

        self._thread = Thread(target=target, daemon=True)
        self._thread.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:

        if self._thread:
            await self._stop_server()

            self._thread.join()
            self._thread = None
        else:
            raise RuntimeError("Server is not running")

    # @staticmethod
    # def from_agent_application(agent_app: AgentApplication) -> ApplicationRunner:
        
    #     adapter = agent_app.get_adapter()