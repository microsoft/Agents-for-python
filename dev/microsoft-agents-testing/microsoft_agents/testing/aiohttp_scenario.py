# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""AiohttpScenario - in-process AgentApplication testing scenario.

Provides a scenario that hosts an already-created AgentApplication within the
test process using aiohttp. The scenario drives the real aiohttp/CloudAdapter
request path while still keeping tests in-process and isolated from a deployed
web server.

Use :meth:`AiohttpScenario.from_app` when a sample or test already defines
module-level AgentApplication components, and use :meth:`AiohttpScenario.create`
when the test wants the scenario to create the standard storage, adapter,
authorization, and connection components before registering handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, cast
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer
from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AgentApplication,
    AnonymousTokenProvider,
    Authorization,
    ChannelServiceAdapter,
    Connections,
    ConnectionManager,
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

from .core import (
    AiohttpCallbackServer,
    _AiohttpClientFactory,
    ClientFactory,
    Scenario,
    ScenarioConfig,
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AgentEnvironment:
    """Components used by an in-process AgentApplication scenario.

    The environment groups the application and the infrastructure objects used
    to host it. Tests can inspect these values directly when they need access to
    storage, authorization, adapter, or connection-manager state.

    Attributes:
        config: SDK configuration dictionary.
        agent_application: AgentApplication instance hosted by the scenario.
        authorization: Authorization handler associated with the application.
        adapter: Channel service adapter used by the aiohttp entry point.
        storage: State storage instance, typically MemoryStorage.
        connections: Connection manager used by the adapter and authorization.
    """

    config: dict
    agent_application: AgentApplication
    authorization: Authorization
    adapter: ChannelServiceAdapter
    storage: Storage
    connections: Connections

class AiohttpScenario(Scenario):
    """Scenario that hosts an AgentApplication in-process using aiohttp.

    Use this scenario for integration-style tests that should exercise the
    real aiohttp route, CloudAdapter, callback server, AgentClient transport,
    and transcript recording without deploying a separate web service.

    The constructor accepts a fully built :class:`AgentEnvironment`. For common
    test setup patterns, prefer the factory helpers:

    - :meth:`create` builds a standard environment and then calls a setup
      function to register routes/handlers.
    - :meth:`from_app` wraps an existing AgentApplication, such as one defined
      at module scope in a sample's ``agents.py`` file.

    Example::

        scenario = AiohttpScenario.from_app(AGENT_APP, use_jwt_middleware=False)

        async with scenario.client() as client:
            await client.send("Hello!", wait=0.2)
            client.expect().that_for_any(type="message")

    :param agent_environment: Application and hosting components to use.
    :param config: Optional scenario configuration.
    :param use_jwt_middleware: Whether to use JWT auth middleware.
    """

    _setup: Callable[[AgentEnvironment], None] | None = None
    _env_factory: Callable[[], AgentEnvironment] | None = None
    _env: AgentEnvironment | None = None

    def __init__(
        self,
        env_or_setup: AgentEnvironment | Callable[[AgentEnvironment], None],
        config: ScenarioConfig | None = None,
        *,
        use_jwt_middleware: bool = True,
        env_factory: Callable[[], AgentEnvironment] | None = None,
    ) -> None:
        super().__init__(config)

        if not env_or_setup:
            raise ValueError("env_or_setup must be provided.")

        self._use_jwt_middleware = use_jwt_middleware
        self._config = config or ScenarioConfig()

        if callable(env_or_setup):
            self._setup = env_or_setup
            self._env_factory = env_factory or (
                lambda: AiohttpScenario._default_env_factory(config=self._config)
            )
        else:
            if env_factory:
                raise ValueError(
                    "env_factory should not be provided when env_or_setup is an AgentEnvironment."
                )
            self._env = env_or_setup

    @property
    def agent_environment(self) -> AgentEnvironment:
        """Get the environment hosted by this scenario.

        For scenarios created with :meth:`create`, the environment is
        constructed lazily on first access so pytest fixtures can inspect agent
        components before a client is opened.
        """
        self._ensure_env()
        if not self._env:
            raise RuntimeError(
                "Agent environment not available. Is the scenario running?"
            )
        return self._env

    def _ensure_env(self) -> None:
        if (
            self._env is None
            and self._setup is not None
            and self._env_factory is not None
        ):
            self._env = self._env_factory()
            self._setup(self._env)

    @classmethod
    def _default_env_factory(
        cls,
        config: ScenarioConfig,
        sdk_config: dict | None = None,
        omit_connections: bool = False,
    ) -> AgentEnvironment:
        """Default factory for creating a standard AgentEnvironment.

        This factory creates MemoryStorage, a connection manager, CloudAdapter,
        Authorization, and AgentApplication. It is used by the :meth:`create`
        factory when no custom environment factory is provided.
        """
        env_vars = dotenv_values(config.env_file_path or ".env")
        sdk_config = load_configuration_from_env(env_vars) if sdk_config is None else sdk_config

        storage = MemoryStorage()

        connection_manager: Connections
        if omit_connections:
            connection_manager = ConnectionManager(
                provider_factory=lambda c: AnonymousTokenProvider(),
                connections_configurations={
                    "SERVICE_CONNECTION": AgentAuthConfiguration(
                        anonymous_allowed=True,
                    )
                }
            )
        else:
            connection_manager = MsalConnectionManager(**sdk_config)

        storage = MemoryStorage()
        adapter = CloudAdapter(connection_manager=connection_manager)
        authorization = Authorization(storage, connection_manager, **sdk_config)
        agent_application = AgentApplication[TurnState](
            storage=storage, adapter=adapter, authorization=authorization, **sdk_config
        )

        return AgentEnvironment(
            config=sdk_config,
            agent_application=agent_application,
            authorization=authorization,
            adapter=adapter,
            storage=storage,
            connections=connection_manager,
        )

    @staticmethod
    def create(
        setup: Callable[[AgentEnvironment], None],
        config: ScenarioConfig | None = None,
        use_jwt_middleware: bool = True,
        sdk_config: dict | None = None,
        omit_connections: bool | None = None,
    ) -> AiohttpScenario:
        """Create a scenario by building a default AgentApplication environment.

        The factory creates MemoryStorage, a connection manager, CloudAdapter,
        Authorization, and AgentApplication, then calls ``setup`` so the caller
        can register handlers on ``env.agent_application``. This is convenient
        for tests that do not already have module-level agent components.

        By default, connection settings are loaded from ``config.env_file_path``
        or ``.env`` and used to construct an MsalConnectionManager. When
        ``use_jwt_middleware=False`` and ``omit_connections`` is not provided,
        anonymous connections are used for local-only in-process tests.

        :param setup: Synchronous function that receives AgentEnvironment and
            registers handlers/routes.
        :param config: Optional scenario configuration.
        :param use_jwt_middleware: Whether to enable JWT middleware on the
            aiohttp route.
        :param sdk_config: Optional pre-loaded SDK configuration. When omitted,
            configuration is loaded from the scenario env file.
        :param omit_connections: Use an anonymous connection manager instead of
            MSAL-backed connections. When omitted, this defaults to ``True`` if
            JWT middleware is disabled.
        :return: A configured AiohttpScenario instance.
        """
        config = config or ScenarioConfig()

        if omit_connections is None:
            omit_connections = not use_jwt_middleware

        def _env_factory() -> AgentEnvironment:
            return AiohttpScenario._default_env_factory(
                config=config, sdk_config=sdk_config, omit_connections=omit_connections
            )
        
        return AiohttpScenario(
            setup,
            config,
            use_jwt_middleware=use_jwt_middleware,
            env_factory=_env_factory,
        )
    
    @staticmethod
    def from_app(
        app: AgentApplication,
        config: ScenarioConfig | None = None,
        use_jwt_middleware: bool = True,
        sdk_config: dict | None = None,
    ) -> AiohttpScenario:
        """Create a scenario from an existing AgentApplication.

        Use this factory for sample-style modules that already define
        AgentApplication and supporting components at module scope. The scenario
        hosts the provided application through its configured adapter and exposes
        the resulting environment for fixtures and inspection.

        :param app: AgentApplication instance to host.
        :param config: Optional scenario configuration.
        :param use_jwt_middleware: Whether to enable JWT middleware on the
            aiohttp route.
        :param sdk_config: Optional SDK configuration used by AgentClient
            creation, such as for auth-token generation.
        :return: A configured AiohttpScenario instance.
        """
        storage = getattr(app, "_storage", None)
        if storage is None:
            storage = getattr(getattr(app, "_options", None), "storage", None)
        if storage is None:
            raise AttributeError("AgentApplication storage could not be resolved.")

        env = AgentEnvironment(
            config=sdk_config or {},
            agent_application=app,
            authorization=app.auth,
            adapter=app.adapter,
            storage=cast(Storage, storage),
            connections=app.connection_manager,
        )
        return AiohttpScenario(env, config, use_jwt_middleware=use_jwt_middleware)

    def _create_application(self) -> Application:
        """Create the aiohttp Application used by this scenario.

        The application exposes ``POST /api/messages`` and forwards requests to
        ``start_agent_process`` with the scenario's AgentApplication and adapter.
        When enabled, JWT middleware is installed exactly as it would be for a
        hosted aiohttp agent.

        :return: A configured aiohttp Application.
        """
        assert self._env is not None
        assert self._env.agent_application is not None

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

        app["agent_configuration"] = (
            self._env.connections.get_default_connection_configuration()
        )
        app["agent_app"] = self._env.agent_application
        app["adapter"] = adapter

        return app

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start the aiohttp agent server and callback server.

        The yielded factory creates AgentClient instances pointed at the
        in-process aiohttp TestServer. The callback server records outbound
        activities into a shared transcript so tests can inspect recent or full
        conversation history.
        """

        self._ensure_env()
        assert self._env is not None

        app = self._create_application()

        # Start response server
        callback_server = AiohttpCallbackServer(self._config.callback_server_port)

        async with callback_server.listen() as transcript:
            async with TestServer(app, port=3978) as server:
                agent_endpoint = f"http://127.0.0.1:{server.port}/api/messages"

                factory = _AiohttpClientFactory(
                    agent_endpoint=agent_endpoint,
                    response_endpoint=callback_server.service_endpoint,
                    sdk_config=self._env.config,
                    default_config=self._config.client_config,
                    transcript=transcript,
                )

                try:
                    yield factory
                finally:
                    await factory.cleanup()

        if self._setup is not None:
            self._env = None
