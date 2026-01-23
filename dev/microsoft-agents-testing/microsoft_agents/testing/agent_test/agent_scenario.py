# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp import ClientSession
from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env

from microsoft_agents.testing.utils import generate_token_from_config

from .agent_client import (
    AgentClient,
    ResponseServer,
    SenderClient
)

from .agent_scenario_config import AgentScenarioConfig


class AgentScenario(ABC):

    def __init__(self, config: AgentScenarioConfig) -> None:
        self._config = config

        env_vars = dotenv_values(self._config.env_file_path)
        self._sdk_config = load_configuration_from_env(env_vars)

    @abstractmethod
    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        raise NotImplementedError()
    
class _HostedAgentScenario(AgentScenario):

    def __init__(self, config: AgentScenarioConfig) -> None:
        super().__init__(config)

    @asynccontextmanager
    async def _create_client(self, agent_endpoint: str) -> AsyncIterator[AgentClient]:

        response_server = ResponseServer(self._config.response_server_port)
        async with response_server.listen() as collector:

            headers = {
                "Content-Type": "application/json",
            }

            try:
                token = generate_token_from_config(self._sdk_config)
                headers["Authorization"] = f"Bearer {token}"
            except Exception as e:
                pass

            async with ClientSession(base_url=agent_endpoint, headers=headers) as session:

                activity_template = self._config.activity_template.with_updates(
                    service_url=response_server.service_endpoint,
                )

                client = AgentClient(
                    SenderClient(session),
                    collector,
                    activity_template=activity_template,
                )

                yield client
    
class ExternalAgentScenario(_HostedAgentScenario):

    def __init__(self, endpoint: str, config: AgentScenarioConfig) -> None:
        super().__init__(config)
        self._endpoint = endpoint

    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        async with self._create_client(self._endpoint) as client:
            yield client