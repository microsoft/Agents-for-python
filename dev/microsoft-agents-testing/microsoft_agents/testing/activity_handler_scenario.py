# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""ActivityHandlerScenario - In-process testing for ActivityHandler-based agents.

Provides a scenario that hosts an ActivityHandler-based agent within the test
process using aiohttp, enabling integration testing of dialog-heavy agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer
from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.core import (
    ActivityHandler,
    ConversationState,
    UserState,
    MemoryStorage,
    Storage,
    ConnectionManager,
    Connections,
    AgentAuthConfiguration,
    AnonymousTokenProvider,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware

from .core import (
    AiohttpCallbackServer,
    _AiohttpClientFactory,
    ClientFactory,
    Scenario,
    ScenarioConfig,
)


@dataclass
class ActivityHandlerEnvironment:
    """Components available when an ActivityHandler-based agent is running.

    Attributes:
        config: SDK configuration dictionary.
        storage: In-memory state storage shared by all state objects.
        conversation_state: Conversation-scoped state accessor.
        user_state: User-scoped state accessor.
        adapter: CloudAdapter instance configured from the scenario environment.
        connections: Connection manager used by the adapter.
        handler: The ActivityHandler instance under test.
    """

    config: dict
    storage: Storage
    conversation_state: ConversationState
    user_state: UserState
    adapter: CloudAdapter
    connections: Connections
    handler: ActivityHandler | None = None


ActivityHandlerSetup = Callable[
    [ActivityHandlerEnvironment],
    None,
]
ActivityHandlerBuilder = Callable[
    [ActivityHandlerEnvironment],
    ActivityHandler,
]


class ActivityHandlerScenario(Scenario):
    """Test scenario for ActivityHandler-based agents.

    Use this scenario when your agent extends ``ActivityHandler`` rather than
    ``AgentApplication``.  The scenario creates ``MemoryStorage``,
    ``ConversationState``, ``UserState``, and a ``CloudAdapter`` backed by the
    configured service connection, then wires them up and hosts the handler on
    an ephemeral aiohttp test server.

    Example::

        def create_handler(env):
            dialog = UserProfileDialog(env.user_state)
            return DialogAgent(env.conversation_state, env.user_state, dialog)

        scenario = ActivityHandlerScenario.create(create_handler)
        async with scenario.client() as client:
            await client.send("hello", wait=1.0)
            client.expect().that_for_any(text="~Please enter")

    The constructor accepts a fully built :class:`ActivityHandlerEnvironment` or
    a setup callback, matching :class:`AiohttpScenario`. For common test setup
    patterns, prefer the factory helpers:

    - :meth:`create` builds the standard environment and then calls a handler
      factory with it.
    - :meth:`from_handler` wraps an already-created ActivityHandler.

    :param env_or_setup: Environment or setup callback to use.
    :param config: Optional scenario configuration.
    :param use_jwt_middleware: Whether to use JWT auth middleware.
    """

    _setup: ActivityHandlerSetup | None = None
    _env_factory: Callable[[], ActivityHandlerEnvironment] | None = None
    _env: ActivityHandlerEnvironment | None = None

    def __init__(
        self,
        env_or_setup: ActivityHandlerEnvironment | ActivityHandlerSetup,
        config: ScenarioConfig | None = None,
        *,
        use_jwt_middleware: bool = True,
        env_factory: Callable[[], ActivityHandlerEnvironment] | None = None,
    ) -> None:
        super().__init__(config)

        if not env_or_setup:
            raise ValueError("env_or_setup must be provided.")

        self._use_jwt_middleware = use_jwt_middleware
        self._config = config or ScenarioConfig()

        if callable(env_or_setup):
            self._setup = env_or_setup
            self._env_factory = env_factory or (
                lambda: ActivityHandlerScenario._default_env_factory(
                    config=self._config
                )
            )
        else:
            if env_factory:
                raise ValueError(
                    "env_factory should not be provided when env_or_setup is "
                    "an ActivityHandlerEnvironment."
                )
            self._env = env_or_setup

    @property
    def environment(self) -> ActivityHandlerEnvironment:
        """Get the environment hosted by this scenario.

        Setup-backed environments are materialized lazily on first access.
        """
        self._ensure_env()
        if not self._env:
            raise RuntimeError(
                "Agent environment not available. Is the scenario running?"
            )
        return self._env

    @classmethod
    def _default_env_factory(
        cls,
        config: ScenarioConfig,
        sdk_config: dict | None = None,
        omit_connections: bool = False,
        handler: ActivityHandler | None = None,
    ) -> ActivityHandlerEnvironment:
        """Default factory for creating a standard ActivityHandler environment."""
        env_vars = dotenv_values(config.env_file_path or ".env")
        sdk_config = (
            load_configuration_from_env(env_vars) if sdk_config is None else sdk_config
        )

        connection_manager: Connections
        if omit_connections:
            connection_manager = ConnectionManager(
                provider_factory=lambda c: AnonymousTokenProvider(),
                connections_configurations={
                    "SERVICE_CONNECTION": AgentAuthConfiguration(
                        anonymous_allowed=True,
                    )
                },
            )
        else:
            connection_manager = MsalConnectionManager(**sdk_config)

        storage = MemoryStorage()
        conv_state = ConversationState(storage)
        user_state = UserState(storage)
        adapter = CloudAdapter(connection_manager=connection_manager)

        return ActivityHandlerEnvironment(
            config=sdk_config,
            storage=storage,
            conversation_state=conv_state,
            user_state=user_state,
            adapter=adapter,
            connections=connection_manager,
            handler=handler,
        )

    @staticmethod
    def create(
        create_handler: ActivityHandlerBuilder,
        config: ScenarioConfig | None = None,
        use_jwt_middleware: bool = True,
        sdk_config: dict | None = None,
        omit_connections: bool | None = None,
    ) -> ActivityHandlerScenario:
        """Create a scenario by building a default ActivityHandler environment.

        The factory creates MemoryStorage, ConversationState, UserState, a
        connection manager, and CloudAdapter, then calls ``create_handler`` to
        create the ActivityHandler under test.

        :param create_handler: Function that receives ActivityHandlerEnvironment
            and returns the ActivityHandler under test.
        :param config: Optional scenario configuration.
        :param use_jwt_middleware: Whether to enable JWT middleware on the
            aiohttp route.
        :param sdk_config: Optional pre-loaded SDK configuration. When omitted,
            configuration is loaded from the scenario env file.
        :param omit_connections: Use an anonymous connection manager instead of
            MSAL-backed connections. When omitted, this defaults to ``True`` if
            JWT middleware is disabled.
        :return: A configured ActivityHandlerScenario instance.
        """
        if not create_handler:
            raise ValueError("create_handler must be provided.")

        config = config or ScenarioConfig()

        if omit_connections is None:
            omit_connections = not use_jwt_middleware

        def _env_factory() -> ActivityHandlerEnvironment:
            return ActivityHandlerScenario._default_env_factory(
                config=config,
                sdk_config=sdk_config,
                omit_connections=omit_connections,
            )

        def setup(env: ActivityHandlerEnvironment) -> None:
            env.handler = create_handler(env)

        return ActivityHandlerScenario(
            setup,
            config,
            use_jwt_middleware=use_jwt_middleware,
            env_factory=_env_factory,
        )

    @staticmethod
    def from_handler(
        handler: ActivityHandler,
        config: ScenarioConfig | None = None,
        use_jwt_middleware: bool = True,
        sdk_config: dict | None = None,
        omit_connections: bool | None = None,
    ) -> ActivityHandlerScenario:
        """Create a scenario from an existing ActivityHandler.

        The factory builds the standard hosting environment around ``handler``.

        :param handler: ActivityHandler instance to host.
        :param config: Optional scenario configuration.
        :param use_jwt_middleware: Whether to enable JWT middleware on the
            aiohttp route.
        :param sdk_config: Optional pre-loaded SDK configuration. When omitted,
            configuration is loaded from the scenario env file.
        :param omit_connections: Use an anonymous connection manager instead of
            MSAL-backed connections. When omitted, this defaults to ``True`` if
            JWT middleware is disabled.
        :return: A configured ActivityHandlerScenario instance.
        """
        if not handler:
            raise ValueError("handler must be provided.")

        config = config or ScenarioConfig()

        if omit_connections is None:
            omit_connections = not use_jwt_middleware

        env = ActivityHandlerScenario._default_env_factory(
            config=config,
            sdk_config=sdk_config,
            omit_connections=omit_connections,
            handler=handler,
        )
        return ActivityHandlerScenario(
            env,
            config,
            use_jwt_middleware=use_jwt_middleware,
        )

    def _validate_env(self) -> None:
        if self._env is None:
            return
        if self._env.handler is None:
            raise RuntimeError(
                "ActivityHandler environment does not have a handler."
            )
        if not isinstance(self._env.handler, ActivityHandler):
            raise TypeError(
                "ActivityHandler environment handler must be an ActivityHandler."
            )

    def _ensure_env(self) -> None:
        if (
            self._env is None
            and self._setup is not None
            and self._env_factory is not None
        ):
            self._env = self._env_factory()
            self._setup(self._env)
        self._validate_env()

    def _create_application(self) -> Application:
        """Create the aiohttp Application used by this scenario.

        The application exposes ``POST /api/messages`` and forwards requests to
        the scenario's ActivityHandler and adapter.
        When enabled, JWT middleware is installed exactly as it would be for a
        hosted aiohttp agent.

        :return: A configured aiohttp Application.
        """
        assert self._env is not None
        assert self._env.handler is not None
        agent = self._env.handler
        adapter = self._env.adapter

        # Create aiohttp app
        middlewares = [jwt_authorization_middleware] if self._use_jwt_middleware else []
        app = Application(middlewares=middlewares)

        async def entry_point(request: Request) -> Response:
            return await adapter.process(request, agent)

        app.router.add_post("/api/messages", entry_point)
        app["agent_configuration"] = (
            self._env.connections.get_default_connection_configuration()
        )
        app["handler"] = agent
        app["adapter"] = adapter

        return app

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start the scenario and yield a client factory.

        The agent server binds to an ephemeral port; the callback server
        (which receives ``send_activity`` calls from the handler) uses the
        port from ``ScenarioConfig.callback_server_port`` (default 9378).
        """
        self._ensure_env()
        assert self._env is not None

        app = self._create_application()

        callback_server = AiohttpCallbackServer(self._config.callback_server_port)

        async with callback_server.listen() as transcript:
            # port=None → aiohttp picks an available ephemeral port
            async with TestServer(app, port=None) as server:
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
