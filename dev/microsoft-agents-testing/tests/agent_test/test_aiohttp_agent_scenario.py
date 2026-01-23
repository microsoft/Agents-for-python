# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp.web import Application

from microsoft_agents.testing.agent_test.aiohttp_agent_scenario import (
    AiohttpAgentScenario,
    AgentEnvironment,
)
from microsoft_agents.testing.agent_test.agent_scenario import _HostedAgentScenario
from microsoft_agents.testing.agent_test.agent_scenario_config import AgentScenarioConfig
from microsoft_agents.testing.agent_test.agent_client import AgentClient


# =============================================================================
# Unit Tests with Mocking
# =============================================================================

class TestAgentEnvironment:
    """Test AgentEnvironment dataclass."""

    def test_agent_environment_creation(self):
        """Test that AgentEnvironment can be created with all required fields."""
        mock_config = {"key": "value"}
        mock_agent_app = MagicMock()
        mock_authorization = MagicMock()
        mock_adapter = MagicMock()
        mock_storage = MagicMock()
        mock_connections = MagicMock()

        env = AgentEnvironment(
            config=mock_config,
            agent_application=mock_agent_app,
            authorization=mock_authorization,
            adapter=mock_adapter,
            storage=mock_storage,
            connections=mock_connections,
        )

        assert env.config == mock_config
        assert env.agent_application == mock_agent_app
        assert env.authorization == mock_authorization
        assert env.adapter == mock_adapter
        assert env.storage == mock_storage
        assert env.connections == mock_connections


class TestAiohttpAgentScenarioInit:
    """Test AiohttpAgentScenario initialization."""

    def test_inherits_from_hosted_agent_scenario(self):
        """Test that AiohttpAgentScenario inherits from _HostedAgentScenario."""
        assert issubclass(AiohttpAgentScenario, _HostedAgentScenario)

    def test_init_raises_when_init_agent_not_provided(self):
        """Test that initialization raises ValueError when init_agent is not provided."""
        with pytest.raises(ValueError, match="init_agent must be provided"):
            AiohttpAgentScenario(init_agent=None)

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            assert isinstance(scenario._config, AgentScenarioConfig)
            assert scenario._init_agent is mock_init_agent
            assert scenario._env is None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            custom_config = AgentScenarioConfig()
            custom_config.env_file_path = "custom.env"
            mock_init_agent = AsyncMock()

            scenario = AiohttpAgentScenario(
                init_agent=mock_init_agent,
                config=custom_config
            )

            assert scenario._config is custom_config

    def test_init_with_jwt_middleware_enabled(self):
        """Test initialization with JWT middleware enabled (default)."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.jwt_authorization_middleware") as mock_jwt:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(
                init_agent=mock_init_agent,
                use_jwt_middleware=True
            )

            assert isinstance(scenario._application, Application)
            assert mock_jwt in scenario._application.middlewares

    def test_init_with_jwt_middleware_disabled(self):
        """Test initialization with JWT middleware disabled."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(
                init_agent=mock_init_agent,
                use_jwt_middleware=False
            )

            assert isinstance(scenario._application, Application)
            assert len(scenario._application.middlewares) == 0

    def test_init_creates_aiohttp_application(self):
        """Test that initialization creates an aiohttp Application."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            assert isinstance(scenario._application, Application)


class TestAiohttpAgentScenarioAgentEnvironment:
    """Test AiohttpAgentScenario.agent_environment property."""

    def test_agent_environment_raises_when_not_set(self):
        """Test that agent_environment raises ValueError when not set up."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            with pytest.raises(ValueError, match="Agent environment has not been set up yet"):
                _ = scenario.agent_environment

    def test_agent_environment_returns_env_when_set(self):
        """Test that agent_environment returns the environment when set."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            # Manually set the environment for testing
            mock_env = MagicMock(spec=AgentEnvironment)
            scenario._env = mock_env

            assert scenario.agent_environment is mock_env


class TestAiohttpAgentScenarioInitComponents:
    """Test AiohttpAgentScenario._init_components method."""

    @pytest.mark.asyncio
    async def test_init_components_creates_environment(self):
        """Test that _init_components creates the agent environment."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage") as mock_storage, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter") as mock_adapter, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization") as mock_auth, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication") as mock_agent_app:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {"test_key": "test_value"}
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_conn_manager_instance = MagicMock()
            mock_conn_manager.return_value = mock_conn_manager_instance
            mock_adapter_instance = MagicMock()
            mock_adapter.return_value = mock_adapter_instance
            mock_auth_instance = MagicMock()
            mock_auth.return_value = mock_auth_instance
            mock_agent_app_instance = MagicMock()
            mock_agent_app.return_value = mock_agent_app_instance

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            await scenario._init_components()

            assert scenario._env is not None
            assert scenario._env.storage is mock_storage_instance
            assert scenario._env.adapter is mock_adapter_instance
            assert scenario._env.authorization is mock_auth_instance
            assert scenario._env.agent_application is mock_agent_app_instance
            assert scenario._env.connections is mock_conn_manager_instance

    @pytest.mark.asyncio
    async def test_init_components_calls_init_agent(self):
        """Test that _init_components calls the init_agent callable."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"):
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            await scenario._init_components()

            mock_init_agent.assert_called_once()
            # Verify the environment was passed to init_agent
            call_args = mock_init_agent.call_args[0]
            assert isinstance(call_args[0], AgentEnvironment)

    @pytest.mark.asyncio
    async def test_init_components_passes_sdk_config_to_components(self):
        """Test that _init_components passes SDK config to components."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization") as mock_auth, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication") as mock_agent_app:
            
            mock_dotenv.return_value = {}
            sdk_config = {"app_id": "test-app-id", "tenant_id": "test-tenant"}
            mock_load_config.return_value = sdk_config

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            await scenario._init_components()

            # Verify SDK config was passed to MsalConnectionManager
            mock_conn_manager.assert_called_once_with(**sdk_config)

    @pytest.mark.asyncio
    async def test_init_components_sets_environment_config(self):
        """Test that _init_components sets the correct config in environment."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"):
            
            mock_dotenv.return_value = {}
            sdk_config = {"key1": "value1", "key2": "value2"}
            mock_load_config.return_value = sdk_config

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            await scenario._init_components()

            assert scenario._env.config == sdk_config


class TestAiohttpAgentScenarioClient:
    """Test AiohttpAgentScenario.client method."""

    @pytest.mark.asyncio
    async def test_client_yields_agent_client(self):
        """Test that client yields an AgentClient."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.TestServer") as mock_test_server, \
             patch.object(AiohttpAgentScenario, "_create_client") as mock_create_client:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock connection manager
            mock_conn_manager_instance = MagicMock()
            mock_conn_manager_instance.get_default_connection_configuration.return_value = {}
            mock_conn_manager.return_value = mock_conn_manager_instance

            # Setup mock test server
            mock_server = MagicMock()
            mock_server.url = "http://localhost:8080"
            mock_test_server.return_value.__aenter__ = AsyncMock(return_value=mock_server)
            mock_test_server.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup mock client
            mock_client = MagicMock(spec=AgentClient)
            mock_create_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_create_client.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            async with scenario.client() as client:
                assert client is mock_client

    @pytest.mark.asyncio
    async def test_client_initializes_components(self):
        """Test that client calls _init_components."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.TestServer") as mock_test_server, \
             patch.object(AiohttpAgentScenario, "_create_client") as mock_create_client:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock connection manager
            mock_conn_manager_instance = MagicMock()
            mock_conn_manager_instance.get_default_connection_configuration.return_value = {}
            mock_conn_manager.return_value = mock_conn_manager_instance

            # Setup mock test server
            mock_server = MagicMock()
            mock_server.url = "http://localhost:8080"
            mock_test_server.return_value.__aenter__ = AsyncMock(return_value=mock_server)
            mock_test_server.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup mock client
            mock_client = MagicMock(spec=AgentClient)
            mock_create_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_create_client.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            async with scenario.client() as client:
                # Verify init_agent was called (which means _init_components ran)
                mock_init_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_adds_message_route(self):
        """Test that client adds the /api/messages route."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.TestServer") as mock_test_server, \
             patch.object(AiohttpAgentScenario, "_create_client") as mock_create_client:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock connection manager
            mock_conn_manager_instance = MagicMock()
            mock_conn_manager_instance.get_default_connection_configuration.return_value = {}
            mock_conn_manager.return_value = mock_conn_manager_instance

            # Setup mock test server
            mock_server = MagicMock()
            mock_server.url = "http://localhost:8080"
            mock_test_server.return_value.__aenter__ = AsyncMock(return_value=mock_server)
            mock_test_server.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup mock client
            mock_client = MagicMock(spec=AgentClient)
            mock_create_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_create_client.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            async with scenario.client() as client:
                # Check that the route was added
                routes = [r.resource.canonical for r in scenario._application.router.routes() if hasattr(r, 'resource')]
                assert "/api/messages" in routes

    @pytest.mark.asyncio
    async def test_client_sets_application_config(self):
        """Test that client sets application configuration."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MemoryStorage"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.MsalConnectionManager") as mock_conn_manager, \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.CloudAdapter"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.Authorization"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.AgentApplication"), \
             patch("microsoft_agents.testing.agent_test.aiohttp_agent_scenario.TestServer") as mock_test_server, \
             patch.object(AiohttpAgentScenario, "_create_client") as mock_create_client:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock connection manager
            mock_conn_manager_instance = MagicMock()
            mock_default_config = {"connection_key": "connection_value"}
            mock_conn_manager_instance.get_default_connection_configuration.return_value = mock_default_config
            mock_conn_manager.return_value = mock_conn_manager_instance

            # Setup mock test server
            mock_server = MagicMock()
            mock_server.url = "http://localhost:8080"
            mock_test_server.return_value.__aenter__ = AsyncMock(return_value=mock_server)
            mock_test_server.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup mock client
            mock_client = MagicMock(spec=AgentClient)
            mock_create_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_create_client.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_init_agent = AsyncMock()
            scenario = AiohttpAgentScenario(init_agent=mock_init_agent)

            async with scenario.client() as client:
                # Verify application configuration was set
                assert "agent_configuration" in scenario._application
                assert "agent_app" in scenario._application
                assert "adapter" in scenario._application


# =============================================================================
# Integration Tests (No Mocking of Core Components)
# =============================================================================

class TestAiohttpAgentScenarioIntegration:
    """Integration tests for AiohttpAgentScenario without mocking core components.
    
    These tests disable JWT middleware and don't rely on bearer token generation.
    """

    @pytest.mark.asyncio
    async def test_scenario_creates_real_environment(self):
        """Test that the scenario creates a real AgentEnvironment with actual components."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            # Provide minimal config that doesn't require real credentials
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            agent_initialized = False

            async def init_agent(env: AgentEnvironment):
                nonlocal agent_initialized
                agent_initialized = True
                # Verify environment has all required components
                assert env.config is not None
                assert env.agent_application is not None
                assert env.authorization is not None
                assert env.adapter is not None
                assert env.storage is not None
                assert env.connections is not None

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,  # Disable JWT middleware
            )

            await scenario._init_components()

            assert agent_initialized
            assert scenario.agent_environment is not None

    @pytest.mark.asyncio
    async def test_scenario_client_starts_test_server(self):
        """Test that the client context manager starts a real test server."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            # Make token generation fail silently (as designed)
            mock_gen_token.side_effect = Exception("No credentials")

            async def init_agent(env: AgentEnvironment):
                pass

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            async with scenario.client() as client:
                assert isinstance(client, AgentClient)
                # Verify the application has the expected routes
                routes = [r.resource.canonical for r in scenario._application.router.routes() if hasattr(r, 'resource')]
                assert "/api/messages" in routes

    @pytest.mark.asyncio
    async def test_scenario_with_custom_init_agent(self):
        """Test that custom init_agent function is called with correct environment."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {"custom_key": "custom_value"}
            mock_gen_token.side_effect = Exception("No credentials")

            received_env = None

            async def init_agent(env: AgentEnvironment):
                nonlocal received_env
                received_env = env

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            async with scenario.client() as client:
                assert received_env is not None
                assert received_env.config == {"custom_key": "custom_value"}

    @pytest.mark.asyncio
    async def test_scenario_application_stores_components(self):
        """Test that the aiohttp application stores agent components correctly."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_gen_token.side_effect = Exception("No credentials")

            async def init_agent(env: AgentEnvironment):
                pass

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            async with scenario.client() as client:
                # Verify application has stored the components
                assert scenario._application["agent_app"] is scenario._env.agent_application
                assert scenario._application["adapter"] is scenario._env.adapter
                assert "agent_configuration" in scenario._application

    @pytest.mark.asyncio
    async def test_scenario_without_jwt_middleware_has_no_middlewares(self):
        """Test that disabling JWT middleware results in no middlewares."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            async def init_agent(env: AgentEnvironment):
                pass

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            assert len(scenario._application.middlewares) == 0

    @pytest.mark.asyncio
    async def test_scenario_agent_environment_accessible_after_init(self):
        """Test that agent_environment property works after initialization."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_gen_token.side_effect = Exception("No credentials")

            async def init_agent(env: AgentEnvironment):
                pass

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            # Before client(), agent_environment should raise
            with pytest.raises(ValueError):
                _ = scenario.agent_environment

            async with scenario.client() as client:
                # After client() starts, agent_environment should be accessible
                env = scenario.agent_environment
                assert env is not None
                assert isinstance(env, AgentEnvironment)

    @pytest.mark.asyncio
    async def test_scenario_with_custom_config(self):
        """Test that custom AgentScenarioConfig is used correctly."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_gen_token.side_effect = Exception("No credentials")

            custom_config = AgentScenarioConfig()
            custom_config.env_file_path = "test.env"
            custom_config.response_server_port = 9999

            async def init_agent(env: AgentEnvironment):
                pass

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                config=custom_config,
                use_jwt_middleware=False,
            )

            assert scenario._config is custom_config
            assert scenario._config.response_server_port == 9999

    @pytest.mark.asyncio
    async def test_multiple_client_sessions_reinitialize_components(self):
        """Test that each client() call reinitializes components."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_gen_token.side_effect = Exception("No credentials")

            init_count = 0

            async def init_agent(env: AgentEnvironment):
                nonlocal init_count
                init_count += 1

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            # Note: The current implementation would call _init_components each time
            # But routes can only be added once to the router, so this tests the first call
            async with scenario.client() as client:
                assert init_count == 1

    @pytest.mark.asyncio
    async def test_init_agent_receives_storage_instance(self):
        """Test that init_agent receives a working storage instance."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}

            storage_works = False

            async def init_agent(env: AgentEnvironment):
                nonlocal storage_works
                # Test that storage is a real MemoryStorage instance
                from microsoft_agents.hosting.core import MemoryStorage
                storage_works = isinstance(env.storage, MemoryStorage)

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            await scenario._init_components()

            assert storage_works

    @pytest.mark.asyncio
    async def test_init_agent_can_configure_agent_application(self):
        """Test that init_agent can configure the agent application."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_gen_token:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_gen_token.side_effect = Exception("No credentials")

            custom_data = {"configured": True}

            async def init_agent(env: AgentEnvironment):
                # Simulate configuring the agent application
                env.agent_application._custom_data = custom_data

            scenario = AiohttpAgentScenario(
                init_agent=init_agent,
                use_jwt_middleware=False,
            )

            async with scenario.client() as client:
                # Verify the custom configuration persists
                assert hasattr(scenario._env.agent_application, "_custom_data")
                assert scenario._env.agent_application._custom_data == custom_data