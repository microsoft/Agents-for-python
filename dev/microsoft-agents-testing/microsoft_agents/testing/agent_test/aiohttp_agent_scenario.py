# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
from dataclasses import dataclass
from typing import Callable, Awaitable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp import ClientSession
from aiohttp.web import Application
from aiohttp.test_utils import TestServer

from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    ChannelServiceAdapter,
    Connections,
    MemoryStorage,
    Storage,
    TurnState,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    start_agent_process,
    jwt_authorization_middleware,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from .agent_client import AgentClient
from .agent_scenario import _HostedAgentScenario
from .agent_scenario_config import AgentScenarioConfig

@dataclass
class AgentEnvironment:

    config: dict

    agent_application: AgentApplication
    authorization: Authorization
    adapter: ChannelServiceAdapter
    storage: Storage
    connections: Connections

class AiohttpAgentScenario(_HostedAgentScenario):

    def __init__(
        self,
        init_agent: Callable[[AgentEnvironment], Awaitable[None]],
        config: AgentScenarioConfig,
        use_jwt_middleware: bool = True,
    ) -> None:
        
        super().__init__(config)
        
        self._init_agent = init_agent

        self._env: AgentEnvironment | None = None

        middlewares = []
        if use_jwt_middleware:
            middlewares.append(jwt_authorization_middleware)
        self._application: Application = Application(middlewares=middlewares)

    @property
    def agent_environment(self) -> AgentEnvironment:
        if not self._env:
            raise ValueError("Agent environment has not been set up yet.")
        return self._env

    async def _init_components(self) -> None:

        storage = MemoryStorage()
        connection_manager = MsalConnectionManager(**self._sdk_config)
        adapter = CloudAdapter(connection_manager=connection_manager)
        authorization = Authorization(
            storage, connection_manager, **self._sdk_config
        )
        agent_application = AgentApplication[TurnState](
            storage=storage,
            adapter=adapter,
            authorization=authorization,
            **self._sdk_config
        )

        self._env = AgentEnvironment(
            config=self._sdk_config,
            agent_application=agent_application,
            authorization=authorization,
            adapter=adapter,
            storage=storage,
            connections=connection_manager
        )
        
        await self._init_agent(self._env)
    
    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:

        await self._init_components()

        self._application.router.add_post(
            "/api/messages", 
            functools.partial(start_agent_process,
                agent_application=self._env.agent_application, 
                adapter=self._env.adapter
            )
        )

        self._application["agent_configuration"] = (
            self._env.connections.get_default_connection_configuration()
        )
        self._application["agent_app"] = self._env.agent_application
        self._application["adapter"] = self._env.adapter


        async with TestServer(self._application) as server:
            async with self._create_client(server.url) as client:
                yield client