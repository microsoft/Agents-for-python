# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from microsoft_agents.activity import Activity

from microsoft_agents.testing.agent_test.agent_scenario import (
    AgentScenario,
    _HostedAgentScenario,
    ExternalAgentScenario,
)
from microsoft_agents.testing.agent_test.agent_scenario_config import AgentScenarioConfig
from microsoft_agents.testing.agent_test.agent_client import AgentClient


class TestAgentScenarioInit:
    """Test AgentScenario initialization."""

    def test_init_with_default_config(self):
        """Test that AgentScenario uses default config when none provided."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Create a concrete implementation for testing
            class ConcreteAgentScenario(AgentScenario):
                async def client(self):
                    pass
            
            scenario = ConcreteAgentScenario()
            
            assert isinstance(scenario._config, AgentScenarioConfig)
            mock_dotenv.assert_called_once_with(AgentScenarioConfig.env_file_path)

    def test_init_with_custom_config(self):
        """Test that AgentScenario uses provided config."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            custom_config = AgentScenarioConfig()
            custom_config.env_file_path = "custom.env"
            
            class ConcreteAgentScenario(AgentScenario):
                async def client(self):
                    pass
            
            scenario = ConcreteAgentScenario(config=custom_config)
            
            assert scenario._config is custom_config
            mock_dotenv.assert_called_once_with("custom.env")

    def test_init_loads_env_configuration(self):
        """Test that initialization loads environment configuration."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            env_vars = {"VAR1": "value1", "VAR2": "value2"}
            mock_dotenv.return_value = env_vars
            mock_load_config.return_value = {"sdk_key": "sdk_value"}
            
            class ConcreteAgentScenario(AgentScenario):
                async def client(self):
                    pass
            
            scenario = ConcreteAgentScenario()
            
            mock_load_config.assert_called_once_with(env_vars)
            assert scenario._sdk_config == {"sdk_key": "sdk_value"}


class TestAgentScenarioClientAbstractMethod:
    """Test that AgentScenario.client is abstract."""

    def test_client_is_abstract(self):
        """Test that AgentScenario cannot be instantiated directly."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values"), \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env"):
            
            # AgentScenario is abstract and should not be instantiated directly
            with pytest.raises(TypeError):
                AgentScenario()


class TestHostedAgentScenarioInit:
    """Test _HostedAgentScenario initialization."""

    def test_init_inherits_from_agent_scenario(self):
        """Test that _HostedAgentScenario inherits from AgentScenario."""
        assert issubclass(_HostedAgentScenario, AgentScenario)

    def test_init_with_default_config(self):
        """Test that _HostedAgentScenario uses default config when none provided."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            # Create a concrete implementation for testing
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    pass
            
            scenario = ConcreteHostedScenario()
            
            assert isinstance(scenario._config, AgentScenarioConfig)


class TestHostedAgentScenarioCreateClient:
    """Test _HostedAgentScenario._create_client method."""

    @pytest.mark.asyncio
    async def test_create_client_yields_agent_client(self):
        """Test that _create_client yields an AgentClient."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "test_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    async with self._create_client("http://test-endpoint") as client:
                        yield client
            
            scenario = ConcreteHostedScenario()
            
            async with scenario._create_client("http://test-endpoint") as client:
                assert isinstance(client, AgentClient)

    @pytest.mark.asyncio
    async def test_create_client_uses_correct_port(self):
        """Test that _create_client uses the configured response server port."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "test_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9999/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            custom_config = AgentScenarioConfig()
            custom_config.response_server_port = 9999
            
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    async with self._create_client("http://test-endpoint") as client:
                        yield client
            
            scenario = ConcreteHostedScenario(config=custom_config)
            
            async with scenario._create_client("http://test-endpoint") as client:
                mock_response_server.assert_called_once_with(9999)

    @pytest.mark.asyncio
    async def test_create_client_sets_authorization_header_with_token(self):
        """Test that _create_client sets the Authorization header when token is generated."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "my_auth_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    async with self._create_client("http://test-endpoint") as client:
                        yield client
            
            scenario = ConcreteHostedScenario()
            
            async with scenario._create_client("http://test-endpoint") as client:
                # Check that ClientSession was called with authorization header
                call_kwargs = mock_client_session.call_args[1]
                assert "headers" in call_kwargs
                assert call_kwargs["headers"]["Authorization"] == "Bearer my_auth_token"
                assert call_kwargs["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_create_client_continues_without_token_on_exception(self):
        """Test that _create_client continues without token if token generation fails."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.side_effect = Exception("Token generation failed")
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    async with self._create_client("http://test-endpoint") as client:
                        yield client
            
            scenario = ConcreteHostedScenario()
            
            # Should not raise, just continue without Authorization header
            async with scenario._create_client("http://test-endpoint") as client:
                call_kwargs = mock_client_session.call_args[1]
                assert "Authorization" not in call_kwargs["headers"]
                assert call_kwargs["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_create_client_uses_correct_agent_endpoint(self):
        """Test that _create_client uses the provided agent endpoint."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "test_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            class ConcreteHostedScenario(_HostedAgentScenario):
                async def client(self):
                    async with self._create_client("http://my-custom-endpoint:8080") as client:
                        yield client
            
            scenario = ConcreteHostedScenario()
            
            async with scenario._create_client("http://my-custom-endpoint:8080") as client:
                call_kwargs = mock_client_session.call_args[1]
                assert call_kwargs["base_url"] == "http://my-custom-endpoint:8080"


class TestExternalAgentScenarioInit:
    """Test ExternalAgentScenario initialization."""

    def test_init_inherits_from_hosted_agent_scenario(self):
        """Test that ExternalAgentScenario inherits from _HostedAgentScenario."""
        assert issubclass(ExternalAgentScenario, _HostedAgentScenario)

    def test_init_sets_endpoint(self):
        """Test that ExternalAgentScenario stores the endpoint."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            scenario = ExternalAgentScenario("http://my-agent-endpoint")
            
            assert scenario._endpoint == "http://my-agent-endpoint"

    def test_init_with_custom_config(self):
        """Test that ExternalAgentScenario uses provided config."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config:
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            
            custom_config = AgentScenarioConfig()
            custom_config.env_file_path = "custom.env"
            
            scenario = ExternalAgentScenario("http://my-agent-endpoint", config=custom_config)
            
            assert scenario._config is custom_config

    def test_init_raises_value_error_when_endpoint_is_empty_string(self):
        """Test that ExternalAgentScenario raises ValueError for empty endpoint."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values"), \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env"):
            
            with pytest.raises(ValueError, match="endpoint must be provided"):
                ExternalAgentScenario("")

    def test_init_raises_value_error_when_endpoint_is_none(self):
        """Test that ExternalAgentScenario raises ValueError for None endpoint."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values"), \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env"):
            
            with pytest.raises(ValueError, match="endpoint must be provided"):
                ExternalAgentScenario(None)


class TestExternalAgentScenarioClient:
    """Test ExternalAgentScenario.client method."""

    @pytest.mark.asyncio
    async def test_client_yields_agent_client(self):
        """Test that client yields an AgentClient."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "test_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            scenario = ExternalAgentScenario("http://my-external-agent")
            
            async with scenario.client() as client:
                assert isinstance(client, AgentClient)

    @pytest.mark.asyncio
    async def test_client_uses_configured_endpoint(self):
        """Test that client uses the configured endpoint."""
        with patch("microsoft_agents.testing.agent_test.agent_scenario.dotenv_values") as mock_dotenv, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.load_configuration_from_env") as mock_load_config, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ResponseServer") as mock_response_server, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.ClientSession") as mock_client_session, \
             patch("microsoft_agents.testing.agent_test.agent_scenario.generate_token_from_config") as mock_generate_token:
            
            mock_dotenv.return_value = {}
            mock_load_config.return_value = {}
            mock_generate_token.return_value = "test_token"
            
            # Setup mock response server
            mock_collector = MagicMock()
            mock_server_instance = MagicMock()
            mock_server_instance.service_endpoint = "http://localhost:9378/v3/conversations/"
            mock_server_instance.listen = MagicMock(return_value=AsyncMock())
            mock_server_instance.listen.return_value.__aenter__ = AsyncMock(return_value=mock_collector)
            mock_server_instance.listen.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_response_server.return_value = mock_server_instance
            
            # Setup mock client session
            mock_session = MagicMock()
            mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            scenario = ExternalAgentScenario("http://my-specific-endpoint:5000")
            
            async with scenario.client() as client:
                call_kwargs = mock_client_session.call_args[1]
                assert call_kwargs["base_url"] == "http://my-specific-endpoint:5000"