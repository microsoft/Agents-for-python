# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ExternalScenario class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from microsoft_agents.testing.core.external_scenario import ExternalScenario
from microsoft_agents.testing.core.scenario import Scenario, ScenarioConfig
from microsoft_agents.testing.core.config import ClientConfig
from microsoft_agents.testing.core._aiohttp_client_factory import _AiohttpClientFactory


# ============================================================================
# ExternalScenario Initialization Tests
# ============================================================================

class TestExternalScenarioInitialization:
    """Tests for ExternalScenario initialization."""

    def test_initialization_with_endpoint(self):
        """ExternalScenario initializes with endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert scenario._endpoint == "http://localhost:3978/api/messages"

    def test_initialization_with_endpoint_and_config(self):
        """ExternalScenario initializes with endpoint and config."""
        config = ScenarioConfig(callback_server_port=9000)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        assert scenario._endpoint == "http://localhost:3978/api/messages"
        assert scenario._config is config
        assert scenario._config.callback_server_port == 9000

    def test_initialization_with_default_config(self):
        """ExternalScenario uses default config when none provided."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert isinstance(scenario._config, ScenarioConfig)
        assert scenario._config.callback_server_port == 9378  # Default port

    def test_initialization_raises_on_empty_endpoint(self):
        """ExternalScenario raises ValueError for empty endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint="")

    def test_initialization_raises_on_none_endpoint(self):
        """ExternalScenario raises ValueError for None endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint=None)

    def test_inherits_from_scenario(self):
        """ExternalScenario inherits from Scenario."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert isinstance(scenario, Scenario)


# ============================================================================
# ExternalScenario Configuration Tests
# ============================================================================

class TestExternalScenarioConfiguration:
    """Tests for ExternalScenario configuration handling."""

    def test_config_with_env_file_path(self):
        """ExternalScenario accepts config with env_file_path."""
        config = ScenarioConfig(env_file_path="/path/to/.env")
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        assert scenario._config.env_file_path == "/path/to/.env"

    def test_config_with_client_config(self):
        """ExternalScenario accepts config with client_config."""
        client_config = ClientConfig(
            headers={"X-Custom": "value"},
            auth_token="test-token",
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        assert scenario._config.client_config.auth_token == "test-token"
        assert scenario._config.client_config.headers == {"X-Custom": "value"}

    def test_config_with_custom_port(self):
        """ExternalScenario uses custom callback_server_port from config."""
        config = ScenarioConfig(callback_server_port=8080)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        assert scenario._config.callback_server_port == 8080


# ============================================================================
# ExternalScenario.run Tests
# ============================================================================

class TestExternalScenarioRun:
    """Tests for ExternalScenario.run method."""

    @pytest.mark.asyncio
    async def test_run_yields_factory(self):
        """run() yields a client factory."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            # Create async context manager mock
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                assert isinstance(factory, _AiohttpClientFactory)

    @pytest.mark.asyncio
    async def test_run_loads_env_from_config_path(self):
        """run() loads environment from config.env_file_path."""
        config = ScenarioConfig(env_file_path="/path/to/.env")
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {"KEY": "value"}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                mock_dotenv.assert_called_once_with("/path/to/.env")

    @pytest.mark.asyncio
    async def test_run_creates_callback_server_with_config_port(self):
        """run() creates callback server with configured port."""
        config = ScenarioConfig(callback_server_port=8080)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:8080/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                mock_server_class.assert_called_once_with(8080)

    @pytest.mark.asyncio
    async def test_run_passes_endpoint_to_factory(self):
        """run() passes endpoint to the client factory."""
        scenario = ExternalScenario(endpoint="http://my-agent:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                assert factory._agent_url == "http://my-agent:3978/api/messages"

    @pytest.mark.asyncio
    async def test_run_passes_service_endpoint_to_factory(self):
        """run() passes callback server's service_endpoint to factory."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                assert factory._response_endpoint == "http://localhost:9378/v3/conversations/"

    @pytest.mark.asyncio
    async def test_run_passes_sdk_config_to_factory(self):
        """run() passes loaded sdk_config to factory."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            expected_sdk_config = {"CONNECTIONS": {"SERVICE_CONNECTION": {"SETTINGS": {}}}}
            mock_dotenv.return_value = {}
            mock_load_config.return_value = expected_sdk_config
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                assert factory._sdk_config is expected_sdk_config

    @pytest.mark.asyncio
    async def test_run_passes_client_config_to_factory(self):
        """run() passes client_config from scenario config to factory."""
        client_config = ClientConfig(auth_token="test-token")
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                assert factory._default_config is client_config


# ============================================================================
# ExternalScenario.run Cleanup Tests
# ============================================================================

class TestExternalScenarioRunCleanup:
    """Tests for ExternalScenario.run cleanup behavior."""

    @pytest.mark.asyncio
    async def test_run_cleans_up_factory_on_exit(self):
        """run() calls factory.cleanup() on context exit."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class, \
             patch("microsoft_agents.testing.core.external_scenario._AiohttpClientFactory") as mock_factory_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            # Setup mock factory
            mock_factory = MagicMock()
            mock_factory.cleanup = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            async with scenario.run() as factory:
                pass  # Just enter and exit
            
            mock_factory.cleanup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_cleans_up_factory_on_exception(self):
        """run() calls factory.cleanup() even when exception occurs."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class, \
             patch("microsoft_agents.testing.core.external_scenario._AiohttpClientFactory") as mock_factory_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            # Setup mock factory
            mock_factory = MagicMock()
            mock_factory.cleanup = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            with pytest.raises(RuntimeError):
                async with scenario.run() as factory:
                    raise RuntimeError("Test exception")
            
            mock_factory.cleanup.assert_awaited_once()


# ============================================================================
# ExternalScenario.client Convenience Method Tests
# ============================================================================

class TestExternalScenarioClient:
    """Tests for ExternalScenario.client convenience method (inherited from Scenario)."""

    @pytest.mark.asyncio
    async def test_client_yields_agent_client(self):
        """client() convenience method yields an AgentClient."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class, \
             patch("microsoft_agents.testing.core.external_scenario._AiohttpClientFactory") as mock_factory_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            # Setup mock factory
            mock_client = MagicMock()
            mock_factory = AsyncMock(return_value=mock_client)
            mock_factory.cleanup = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            async with scenario.client() as client:
                assert client is mock_client
                mock_factory.assert_awaited_once_with(None)

    @pytest.mark.asyncio
    async def test_client_passes_config_to_factory(self):
        """client() passes config to factory.__call__."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        custom_config = ClientConfig(auth_token="custom-token")
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class, \
             patch("microsoft_agents.testing.core.external_scenario._AiohttpClientFactory") as mock_factory_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            # Setup mock factory
            mock_client = MagicMock()
            mock_factory = AsyncMock(return_value=mock_client)
            mock_factory.cleanup = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            async with scenario.client(config=custom_config) as client:
                mock_factory.assert_awaited_once_with(custom_config)


# ============================================================================
# ExternalScenario Edge Cases Tests
# ============================================================================

class TestExternalScenarioEdgeCases:
    """Tests for ExternalScenario edge cases."""

    def test_endpoint_with_trailing_slash(self):
        """ExternalScenario accepts endpoint with trailing slash."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages/")
        
        assert scenario._endpoint == "http://localhost:3978/api/messages/"

    def test_endpoint_with_https(self):
        """ExternalScenario accepts https endpoint."""
        scenario = ExternalScenario(endpoint="https://my-agent.azurewebsites.net/api/messages")
        
        assert scenario._endpoint == "https://my-agent.azurewebsites.net/api/messages"

    def test_endpoint_with_port(self):
        """ExternalScenario accepts endpoint with explicit port."""
        scenario = ExternalScenario(endpoint="http://localhost:8080/api/messages")
        
        assert scenario._endpoint == "http://localhost:8080/api/messages"

    @pytest.mark.asyncio
    async def test_run_with_none_env_file_path(self):
        """run() handles None env_file_path."""
        config = ScenarioConfig(env_file_path=None)
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        with patch("microsoft_agents.testing.core.external_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.core.external_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.core.external_scenario.AiohttpCallbackServer") as mock_server_class:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Setup mock callback server
            mock_server = MagicMock()
            mock_server.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_transcript = MagicMock()
            
            mock_listen_cm = AsyncMock()
            mock_listen_cm.__aenter__.return_value = mock_transcript
            mock_listen_cm.__aexit__.return_value = None
            mock_server.listen.return_value = mock_listen_cm
            
            mock_server_class.return_value = mock_server
            
            async with scenario.run() as factory:
                mock_dotenv.assert_called_once_with(None)


# ============================================================================
# ExternalScenario Dataclass/Attribute Tests  
# ============================================================================

class TestExternalScenarioAttributes:
    """Tests for ExternalScenario attributes and properties."""

    def test_endpoint_stored_as_private_attribute(self):
        """Endpoint is stored as _endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert hasattr(scenario, "_endpoint")
        assert scenario._endpoint == "http://localhost:3978/api/messages"

    def test_config_stored_as_private_attribute(self):
        """Config is stored as _config."""
        config = ScenarioConfig()
        scenario = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=config,
        )
        
        assert hasattr(scenario, "_config")
        assert scenario._config is config
