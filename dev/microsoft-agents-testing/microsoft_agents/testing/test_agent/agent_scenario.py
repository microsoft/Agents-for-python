from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from .agent_client import AgentClient
from .agent_scenario_config import AgentScenarioConfig

class AgentScenario(ABC):

    def __init__(self, config: AgentScenarioConfig) -> None:
        self._config = config

    @abstractmethod
    @asynccontextmanager
    async def create_client(self) -> AsyncIterator[AgentClient]:
        raise NotImplementedError()
    
class ExternalAgentScenario(AgentScenario):

    def __init__(self, endpoint: str, config: AgentScenarioConfig) -> None:
        super().__init__(config)
        self._endpoint = endpoint

    @asynccontextmanager
    async def run(self) -> AsyncIterator[AgentClient]:
        yield AgentClient(self._endpoint)
