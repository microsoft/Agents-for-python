# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ActivityHandlerScenario class."""

import pytest

from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from microsoft_agents.testing.activity_handler_scenario import (
    ActivityHandlerEnvironment,
    ActivityHandlerScenario,
)
from microsoft_agents.hosting.aiohttp import jwt_authorization_middleware
from microsoft_agents.testing.core import Scenario, ScenarioConfig


class EchoHandler(ActivityHandler):
    """Simple ActivityHandler used by scenario tests."""

    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(f"Echo: {turn_context.activity.text}")


class TestActivityHandlerEnvironment:
    """Tests for the ActivityHandlerEnvironment dataclass."""

    def test_environment_is_dataclass_with_expected_fields(self):
        """ActivityHandlerEnvironment stores hosting components."""
        handler = EchoHandler()
        env = ActivityHandlerEnvironment(
            config={"key": "value"},
            storage=None,
            conversation_state=None,
            user_state=None,
            adapter=None,
            connections=None,
            handler=handler,
        )

        assert env.config == {"key": "value"}
        assert env.storage is None
        assert env.conversation_state is None
        assert env.user_state is None
        assert env.adapter is None
        assert env.connections is None
        assert env.handler is handler

    def test_environment_handler_can_be_none_during_setup(self):
        """ActivityHandlerEnvironment can be created before the handler exists."""
        env = ActivityHandlerEnvironment(
            config={},
            storage=None,
            conversation_state=None,
            user_state=None,
            adapter=None,
            connections=None,
        )

        assert env.handler is None


class TestActivityHandlerScenarioInitialization:
    """Tests for ActivityHandlerScenario initialization."""

    def test_constructor_accepts_setup_callback(self):
        """ActivityHandlerScenario accepts an environment setup callback."""

        def setup(env: ActivityHandlerEnvironment):
            env.handler = EchoHandler()

        scenario = ActivityHandlerScenario(setup)
        env = scenario.environment

        assert isinstance(scenario, Scenario)
        assert isinstance(env.handler, EchoHandler)
        assert scenario._use_jwt_middleware is True

    def test_create_initializes_with_handler_factory(self):
        """ActivityHandlerScenario.create stores a normalized setup callback."""

        def create_handler(env: ActivityHandlerEnvironment):
            return EchoHandler()

        scenario = ActivityHandlerScenario.create(create_handler)

        assert scenario._setup is not None
        assert scenario._use_jwt_middleware is True
        assert scenario._env is None

    def test_initialization_with_config(self):
        """ActivityHandlerScenario initializes with custom config."""

        def create_handler(env: ActivityHandlerEnvironment):
            return EchoHandler()

        config = ScenarioConfig(callback_server_port=9000)
        scenario = ActivityHandlerScenario.create(create_handler, config=config)

        assert scenario._config is config
        assert scenario._config.callback_server_port == 9000

    def test_create_raises_on_none_setup(self):
        """ActivityHandlerScenario.create raises ValueError for None handler factory."""
        with pytest.raises(ValueError, match="create_handler must be provided"):
            ActivityHandlerScenario.create(None)

    def test_from_handler_uses_existing_handler(self):
        """ActivityHandlerScenario.from_handler hosts an existing handler."""
        handler = EchoHandler()

        scenario = ActivityHandlerScenario.from_handler(
            handler,
            use_jwt_middleware=False,
            sdk_config={},
        )

        assert scenario.environment.handler is handler
        assert scenario._use_jwt_middleware is False

    def test_from_handler_raises_on_none_handler(self):
        """ActivityHandlerScenario.from_handler requires a handler."""
        with pytest.raises(ValueError, match="handler must be provided"):
            ActivityHandlerScenario.from_handler(None)

    def test_constructor_raises_on_none_setup_or_environment(self):
        """ActivityHandlerScenario raises ValueError for None input."""
        with pytest.raises(ValueError, match="env_or_setup must be provided"):
            ActivityHandlerScenario(None)


class TestActivityHandlerScenarioProperties:
    """Tests for ActivityHandlerScenario properties."""

    def test_environment_materializes_setup_environment(self):
        """environment creates a setup-backed environment on first access."""

        def create_handler(env: ActivityHandlerEnvironment):
            return EchoHandler()

        scenario = ActivityHandlerScenario.create(
            create_handler,
            use_jwt_middleware=False,
            sdk_config={},
        )

        env = scenario.environment

        assert env is scenario._env
        assert isinstance(env.handler, EchoHandler)
        assert env.config == {}

    def test_constructor_setup_can_assign_handler(self):
        """constructor setup can assign env.handler."""

        def setup(env: ActivityHandlerEnvironment):
            env.handler = EchoHandler()

        scenario = ActivityHandlerScenario(
            setup,
            use_jwt_middleware=False,
        )

        assert isinstance(scenario.environment.handler, EchoHandler)

    def test_environment_raises_when_factory_does_not_create_handler(self):
        """environment requires create to configure a handler."""

        def create_handler(env: ActivityHandlerEnvironment):
            return None

        scenario = ActivityHandlerScenario.create(
            create_handler,
            use_jwt_middleware=False,
        )

        with pytest.raises(
            RuntimeError,
            match="ActivityHandler environment does not have a handler.",
        ):
            _ = scenario.environment

    def test_environment_raises_when_setup_assigns_invalid_handler(self):
        """environment requires env.handler to be an ActivityHandler."""

        def setup(env: ActivityHandlerEnvironment):
            env.handler = object()

        scenario = ActivityHandlerScenario(
            setup,
            use_jwt_middleware=False,
        )

        with pytest.raises(TypeError, match="handler must be an ActivityHandler"):
            _ = scenario.environment

    def test_create_application_uses_jwt_middleware_when_enabled(self):
        """_create_application uses the same JWT middleware toggle as AiohttpScenario."""
        scenario = ActivityHandlerScenario.from_handler(EchoHandler())

        app = scenario._create_application()

        assert list(app.middlewares) == [jwt_authorization_middleware]

    def test_create_application_has_no_middleware_when_jwt_disabled(self):
        """_create_application does not install anonymous auth middleware."""
        scenario = ActivityHandlerScenario.from_handler(
            EchoHandler(),
            use_jwt_middleware=False,
            sdk_config={},
        )

        app = scenario._create_application()

        assert list(app.middlewares) == []


class TestActivityHandlerScenarioIntegration:
    """Integration tests with real ActivityHandler instances."""

    @pytest.mark.asyncio
    async def test_echo_handler_responds_to_message(self):
        """ActivityHandlerScenario hosts an ActivityHandler in-process."""

        def create_handler(env: ActivityHandlerEnvironment):
            return EchoHandler()

        scenario = ActivityHandlerScenario.create(
            create_handler,
            use_jwt_middleware=False,
        )

        async with scenario.client() as client:
            await client.send("Hello, Handler!", wait=0.2)

            client.expect().that_for_any(text="Echo: Hello, Handler!")
