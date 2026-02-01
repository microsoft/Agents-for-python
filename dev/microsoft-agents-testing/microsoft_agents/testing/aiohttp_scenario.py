from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Awaitable, cast
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer
from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import (
    AgentApplication, Authorization, ChannelServiceAdapter,
    Connections, MemoryStorage, Storage, TurnState,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter, start_agent_process, jwt_authorization_middleware,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from .core import (
    AiohttpCallbackServer,
    _AiohttpClientFactory,
    ClientFactory,
    Scenario,
    ScenarioConfig,
)


@dataclass
class AgentEnvironment:
    """Components available when the agent is running."""
    config: dict
    agent_application: AgentApplication
    authorization: Authorization
    adapter: ChannelServiceAdapter
    storage: Storage
    connections: Connections

class AiohttpScenario(Scenario):
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

    async def _init_agent_environment(self) -> dict:
        """Initialize agent components, return SDK config."""
        
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
    
    def _create_application(self) -> Application:
        """Initialize and return the aiohttp application."""
        assert self._env is not None
        
        # Create aiohttp app
        middlewares = [jwt_authorization_middleware] if self._use_jwt_middleware else []
        app = Application(middlewares=middlewares)
        adapter = cast(CloudAdapter, self._env.adapter)
        async def entry_point(request: Request) -> Response:
            return await start_agent_process(
                request,
                agent_application=self._env.agent_application,
                adapter=adapter,
            )
        app.router.add_post(
            "/api/messages",
            entry_point,
        )

        return app

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start the scenario and yield a client factory."""
        
        sdk_config = await self._init_agent_environment()
        app = self._create_application()
        
        # Start response server
        callback_server = AiohttpCallbackServer(self._config.callback_server_port)

        async with callback_server.listen() as transcript:
            async with TestServer(app, port=3978) as server:
                agent_url = f"http://{server.host}:{server.port}/"
                
                factory = _AiohttpClientFactory(
                    agent_url=agent_url,
                    response_endpoint=callback_server.service_endpoint,
                    sdk_config=sdk_config,
                    default_config=self._config.client_config,
                    transcript=transcript,
                )
                
                try:
                    yield factory
                finally:
                    await factory.cleanup()