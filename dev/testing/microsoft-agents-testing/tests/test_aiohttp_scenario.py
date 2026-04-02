# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the AiohttpScenario class."""

import pytest

from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment
from microsoft_agents.testing.core import Scenario, ScenarioConfig


# ============================================================================
# AgentEnvironment Tests
# ============================================================================


class TestAgentEnvironment:
    """Tests for the AgentEnvironment dataclass."""

    def test_agent_environment_is_dataclass(self):
        """AgentEnvironment is a dataclass with expected fields."""
        env = AgentEnvironment(
            config={"key": "value"},
            agent_application=None,
            authorization=None,
            adapter=None,
            storage=None,
            connections=None,
        )

        assert env.config == {"key": "value"}
        assert env.agent_application is None
        assert env.authorization is None
        assert env.adapter is None
        assert env.storage is None
        assert env.connections is None

    def test_agent_environment_stores_config_dict(self):
        """AgentEnvironment stores the config dictionary."""
        config = {"APP_ID": "test-app", "APP_SECRET": "secret"}
        env = AgentEnvironment(
            config=config,
            agent_application=None,
            authorization=None,
            adapter=None,
            storage=None,
            connections=None,
        )

        assert env.config is config
        assert env.config["APP_ID"] == "test-app"


# ============================================================================
# AiohttpScenario Initialization Tests
# ============================================================================


class TestAiohttpScenarioInitialization:
    """Tests for AiohttpScenario initialization."""

    def test_initialization_with_init_agent(self):
        """AiohttpScenario initializes with init_agent callback."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        assert scenario._init_agent is init_agent

    def test_initialization_with_config(self):
        """AiohttpScenario initializes with custom config."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        config = ScenarioConfig(callback_server_port=9000)
        scenario = AiohttpScenario(init_agent=init_agent, config=config)

        assert scenario._config is config
        assert scenario._config.callback_server_port == 9000

    def test_initialization_with_default_config(self):
        """AiohttpScenario uses default config when none provided."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        assert isinstance(scenario._config, ScenarioConfig)
        assert scenario._config.callback_server_port == 9378

    def test_initialization_raises_on_none_init_agent(self):
        """AiohttpScenario raises ValueError for None init_agent."""
        with pytest.raises(ValueError, match="init_agent must be provided"):
            AiohttpScenario(init_agent=None)

    def test_initialization_with_jwt_middleware_enabled(self):
        """AiohttpScenario initializes with JWT middleware enabled by default."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        assert scenario._use_jwt_middleware is True

    def test_initialization_with_jwt_middleware_disabled(self):
        """AiohttpScenario can disable JWT middleware."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent, use_jwt_middleware=False)

        assert scenario._use_jwt_middleware is False

    def test_inherits_from_scenario(self):
        """AiohttpScenario inherits from Scenario."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        assert isinstance(scenario, Scenario)

    def test_env_is_none_before_run(self):
        """AiohttpScenario._env is None before run() is called."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        assert scenario._env is None


# ============================================================================
# AiohttpScenario Configuration Tests
# ============================================================================


class TestAiohttpScenarioConfiguration:
    """Tests for AiohttpScenario configuration handling."""

    def test_config_with_env_file_path(self):
        """AiohttpScenario accepts config with env_file_path."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        config = ScenarioConfig(env_file_path="/path/to/.env")
        scenario = AiohttpScenario(init_agent=init_agent, config=config)

        assert scenario._config.env_file_path == "/path/to/.env"

    def test_config_with_custom_port(self):
        """AiohttpScenario accepts config with custom callback_server_port."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        config = ScenarioConfig(callback_server_port=8000)
        scenario = AiohttpScenario(init_agent=init_agent, config=config)

        assert scenario._config.callback_server_port == 8000


# ============================================================================
# AiohttpScenario Property Tests
# ============================================================================


class TestAiohttpScenarioProperties:
    """Tests for AiohttpScenario properties."""

    def test_agent_environment_raises_when_not_running(self):
        """agent_environment raises RuntimeError when scenario is not running."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        with pytest.raises(
            RuntimeError, match="Agent environment not available. Is the scenario running?"
        ):
            _ = scenario.agent_environment

    def test_agent_environment_returns_env_when_set(self):
        """agent_environment returns _env when it's set."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario = AiohttpScenario(init_agent=init_agent)

        # Manually set _env for testing the property
        test_env = AgentEnvironment(
            config={},
            agent_application=None,
            authorization=None,
            adapter=None,
            storage=None,
            connections=None,
        )
        scenario._env = test_env

        assert scenario.agent_environment is test_env


# ============================================================================
# AiohttpScenario Init Agent Callback Tests
# ============================================================================


class TestAiohttpScenarioInitAgentCallback:
    """Tests for AiohttpScenario init_agent callback handling."""

    def test_stores_sync_callable_as_init_agent(self):
        """AiohttpScenario stores the provided init_agent callable."""

        async def my_init_agent(env: AgentEnvironment) -> None:
            env.config["initialized"] = True

        scenario = AiohttpScenario(init_agent=my_init_agent)

        assert scenario._init_agent is my_init_agent

    def test_accepts_lambda_as_init_agent(self):
        """AiohttpScenario accepts lambda as init_agent."""
        init_agent = lambda env: None  # noqa: E731

        # Note: This would fail at runtime since it's not async,
        # but initialization should succeed
        scenario = AiohttpScenario(init_agent=init_agent)

        assert scenario._init_agent is init_agent

    def test_accepts_async_function_as_init_agent(self):
        """AiohttpScenario accepts async function as init_agent."""

        async def async_init_agent(env: AgentEnvironment) -> None:
            await some_async_operation()  # noqa: F821 - intentionally undefined

        scenario = AiohttpScenario(init_agent=async_init_agent)

        assert scenario._init_agent is async_init_agent


# ============================================================================
# AiohttpScenario Edge Cases Tests
# ============================================================================


class TestAiohttpScenarioEdgeCases:
    """Tests for AiohttpScenario edge cases."""

    def test_initialization_with_all_parameters(self):
        """AiohttpScenario initializes correctly with all parameters."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        config = ScenarioConfig(
            env_file_path="/custom/.env",
            callback_server_port=7000,
        )

        scenario = AiohttpScenario(
            init_agent=init_agent,
            config=config,
            use_jwt_middleware=False,
        )

        assert scenario._init_agent is init_agent
        assert scenario._config is config
        assert scenario._config.env_file_path == "/custom/.env"
        assert scenario._config.callback_server_port == 7000
        assert scenario._use_jwt_middleware is False

    def test_multiple_scenario_instances_are_independent(self):
        """Multiple AiohttpScenario instances are independent."""

        async def init_agent_1(env: AgentEnvironment) -> None:
            pass

        async def init_agent_2(env: AgentEnvironment) -> None:
            pass

        config1 = ScenarioConfig(callback_server_port=9001)
        config2 = ScenarioConfig(callback_server_port=9002)

        scenario1 = AiohttpScenario(init_agent=init_agent_1, config=config1)
        scenario2 = AiohttpScenario(
            init_agent=init_agent_2, config=config2, use_jwt_middleware=False
        )

        assert scenario1._init_agent is init_agent_1
        assert scenario2._init_agent is init_agent_2
        assert scenario1._config.callback_server_port == 9001
        assert scenario2._config.callback_server_port == 9002
        assert scenario1._use_jwt_middleware is True
        assert scenario2._use_jwt_middleware is False

    def test_config_is_not_shared_between_instances(self):
        """Config is not shared between scenario instances."""

        async def init_agent(env: AgentEnvironment) -> None:
            pass

        scenario1 = AiohttpScenario(init_agent=init_agent)
        scenario2 = AiohttpScenario(init_agent=init_agent)

        assert scenario1._config is not scenario2._config
