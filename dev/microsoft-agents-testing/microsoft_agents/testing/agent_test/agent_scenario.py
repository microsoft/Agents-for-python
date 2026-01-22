from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp import ClientSession

from .agent_client import (
    AgentClient,
    ResponseServer,
    SenderClient
)

from .agent_scenario_config import AgentScenarioConfig

class AgentScenario(ABC):

    def __init__(self, config: AgentScenarioConfig) -> None:
        self._config = config

    @abstractmethod
    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        raise NotImplementedError()
    
class ExternalAgentScenario(AgentScenario):

    def __init__(self, endpoint: str, config: AgentScenarioConfig) -> None:
        super().__init__(config)
        self._endpoint = endpoint

    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        response_server = ResponseServer(self._endpoint)
        async with response_server.listen() as collector:
            async with ClientSession(base_url=self._endpoint) as session:
                client = AgentClient(
                    SenderClient(session),
                    collector,
                    agent_client_config=self._config
                )
                yield client
