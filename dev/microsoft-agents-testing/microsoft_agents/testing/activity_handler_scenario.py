# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""ActivityHandlerScenario - In-process testing for ActivityHandler-based agents.

Provides a scenario that hosts an ActivityHandler-based agent within the test
process using aiohttp, enabling integration testing of dialog-heavy agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Awaitable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp.web import Application, Request, Response, middleware
from aiohttp.test_utils import TestServer

from microsoft_agents.hosting.core import (
    ActivityHandler,
    ConversationState,
    UserState,
    MemoryStorage,
    Storage,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.aiohttp import CloudAdapter

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
        storage: In-memory state storage shared by all state objects.
        conversation_state: Conversation-scoped state accessor.
        user_state: User-scoped state accessor.
        adapter: CloudAdapter instance (anonymous auth, no real credentials).
        handler: The ActivityHandler instance under test.
    """

    storage: Storage
    conversation_state: ConversationState
    user_state: UserState
    adapter: CloudAdapter
    handler: ActivityHandler


class ActivityHandlerScenario(Scenario):
    """Test scenario for ActivityHandler-based agents.

    Use this scenario when your agent extends ``ActivityHandler`` rather than
    ``AgentApplication``.  The scenario creates ``MemoryStorage``,
    ``ConversationState``, ``UserState``, and a ``CloudAdapter`` (no auth), then
    wires them up and hosts the handler on an ephemeral aiohttp test server.

    Example::

        def create_agent(conv_state, user_state, storage):
            dialog = UserProfileDialog(user_state)
            return DialogAgent(conv_state, user_state, dialog)

        scenario = ActivityHandlerScenario(create_agent)
        async with scenario.client() as client:
            await client.send("hello", wait=1.0)
            client.expect().that_for_any(text="~Please enter")

    :param create_handler: A callable that receives ``(conv_state, user_state,
        storage)`` and returns an ``ActivityHandler`` (sync or async factory).
    :param config: Optional scenario configuration.
    """

    def __init__(
        self,
        create_handler: Callable[
            [ConversationState, UserState, Storage],
            ActivityHandler | Awaitable[ActivityHandler],
        ],
        config: ScenarioConfig | None = None,
    ) -> None:
        super().__init__(config)
        if not create_handler:
            raise ValueError("create_handler must be provided.")
        self._create_handler = create_handler
        self._env: ActivityHandlerEnvironment | None = None

    @property
    def environment(self) -> ActivityHandlerEnvironment:
        """Get the agent environment (only valid while the scenario is running)."""
        if self._env is None:
            raise RuntimeError(
                "Agent environment not available. Is the scenario running?"
            )
        return self._env

    async def _setup(self) -> None:
        """Create storage, state objects, adapter, and handler."""
        storage = MemoryStorage()
        conv_state = ConversationState(storage)
        user_state = UserState(storage)
        adapter = CloudAdapter()

        result = self._create_handler(conv_state, user_state, storage)
        if hasattr(result, "__await__"):
            handler = await result  # type: ignore[misc]
        else:
            handler = result  # type: ignore[assignment]

        self._env = ActivityHandlerEnvironment(
            storage=storage,
            conversation_state=conv_state,
            user_state=user_state,
            adapter=adapter,
            handler=handler,
        )

    def _build_app(self) -> Application:
        """Build the aiohttp Application with an /api/messages POST route.

        An anonymous-identity middleware is applied so that the adapter's
        auth pipeline succeeds without real credentials.  The middleware sets
        ``request["claims_identity"]`` to an unauthenticated anonymous
        ``ClaimsIdentity``, which causes the adapter to skip token acquisition
        and use an empty bearer token for outbound calls (acceptable for
        in-process integration tests where ``serviceUrl`` is the local
        callback server).
        """
        assert self._env is not None
        agent = self._env.handler
        adapter = self._env.adapter

        _anonymous = ClaimsIdentity({}, False, authentication_type="Anonymous")

        @middleware
        async def anonymous_auth(request: Request, handler):
            request["claims_identity"] = _anonymous
            return await handler(request)

        app = Application(middlewares=[anonymous_auth])

        async def entry_point(request: Request) -> Response:
            return await adapter.process(request, agent)

        app.router.add_post("/api/messages", entry_point)
        return app

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start the scenario and yield a client factory.

        The agent server binds to an ephemeral port; the callback server
        (which receives ``send_activity`` calls from the handler) uses the
        port from ``ScenarioConfig.callback_server_port`` (default 9378).
        """
        await self._setup()
        app = self._build_app()

        callback_server = AiohttpCallbackServer(self._config.callback_server_port)

        async with callback_server.listen() as transcript:
            # port=None → aiohttp picks an available ephemeral port
            async with TestServer(app, port=None) as server:
                agent_endpoint = f"http://127.0.0.1:{server.port}/api/messages"

                factory = _AiohttpClientFactory(
                    agent_endpoint=agent_endpoint,
                    response_endpoint=callback_server.service_endpoint,
                    sdk_config={},
                    default_config=self._config.client_config,
                    transcript=transcript,
                )

                try:
                    yield factory
                finally:
                    await factory.cleanup()
