from __future__ import annotations
import functools
from dataclasses import dataclass
from typing import Callable, Awaitable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp import ClientSession
from aiohttp.web import Application
from aiohttp.test_utils import TestServer

from microsoft_agents.hosting.core import (
    AgentApplication, Authorization, ChannelServiceAdapter,
    Connections, MemoryStorage, Storage, TurnState,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter, start_agent_process, jwt_authorization_middleware,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from microsoft_agents.testing.utils import ActivityTemplate, generate_token_from_config
from microsoft_agents.testing.client import AgentClient
from microsoft_agents.testing.client.client_config import ClientConfig
from microsoft_agents.testing.client.transport.aiohttp_sender import AiohttpActivitySender
from microsoft_agents.testing.client.receiver.aiohttp_server import AiohttpResponseServer

from .base import AgentScenario, ScenarioConfig


@dataclass
class AgentEnvironment:
    """Components available when the agent is running."""
    config: dict
    agent_application: AgentApplication
    authorization: Authorization
    adapter: ChannelServiceAdapter
    storage: Storage
    connections: Connections

class AiohttpAgentScenario(AgentScenario):
    """Agent test scenario for an agent hosted within an aiohttp application."""

    def __init__(
        self,
        init_agent: Callable[[AgentEnvironment], Awaitable[None]],
        config: ScenarioConfig | None = None,
        use_jwt_middleware: bool = True,
    ) -> None:
        super().__init__(config)
        
        if not init_agent:
            raise ValueError("init_agent must be provided.")
        
        self._init_agent = init_agent
        self._use_jwt_middleware = use_jwt_middleware
        self._env: AgentEnvironment | None = None

    @property
    def agent_environment(self) -> AgentEnvironment:
        """Get the agent environment (only valid while scenario is running)."""
        if not self._env:
            raise RuntimeError("Agent environment not available. Is the scenario running?")
        return self._env

    async def _init_components(self) -> dict:
        """Initialize agent components, return SDK config."""
        from dotenv import dotenv_values
        from microsoft_agents.activity import load_configuration_from_env
        
        env_vars = dotenv_values(self._config.env_file_path)
        sdk_config = load_configuration_from_env(env_vars)
        
        storage = MemoryStorage()
        connection_manager = MsalConnectionManager(**sdk_config)
        adapter = CloudAdapter(connection_manager=connection_manager)
        authorization = Authorization(storage, connection_manager, **sdk_config)
        agent_application = AgentApplication[TurnState](
            storage=storage, adapter=adapter, authorization=authorization, **sdk_config
        )
        
        self._env = AgentEnvironment(
            config=sdk_config,
            agent_application=agent_application,
            authorization=authorization,
            adapter=adapter,
            storage=storage,
            connections=connection_manager,
        )
        
        await self._init_agent(self._env)
        return sdk_config

    @asynccontextmanager
    async def run(self) -> AsyncIterator[AiohttpClientFactory]:
        """Start the scenario and yield a client factory."""
        
        sdk_config = await self._init_components()
        
        # Create aiohttp app
        middlewares = [jwt_authorization_middleware] if self._use_jwt_middleware else []
        app = Application(middlewares=middlewares)
        app.router.add_post(
            "/api/messages",
            functools.partial(
                start_agent_process,
                agent_application=self._env.agent_application,
                adapter=self._env.adapter,
            ),
        )
        
        # Start response server
        response_server = AiohttpResponseServer(self._config.response_server_port)
        
        async with response_server.start() as receiver:
            async with TestServer(app, port=3978) as server:
                agent_url = f"http://{server.host}:{server.port}/"
                
                factory = AiohttpClientFactory(
                    agent_url=agent_url,
                    response_endpoint=response_server.service_endpoint,
                    sdk_config=sdk_config,
                    default_template=self._config.default_activity_template,
                    default_config=self._config.default_client_config,
                    response_receiver=receiver,
                )
                
                try:
                    yield factory
                finally:
                    await factory.cleanup()