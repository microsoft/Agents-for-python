from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncContextManager, Callable, Awaitable

from abc import ABC, abstractmethod

from .components import TestClient

class AgentScenario(ABC):

    def __init__(self, config: dict):
        self._config = config

    @abstractmethod
    async def _init_agent_application(self):
        pass

    @abstractmethod
    @asynccontextmanager
    async def run(self):
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_fixtures(self) -> list[Callable]:
        return []