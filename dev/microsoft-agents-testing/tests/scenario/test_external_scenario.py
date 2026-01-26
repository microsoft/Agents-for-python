"""
Unit tests for the ExternalScenario class.

This module tests:
- ExternalScenario initialization
- Endpoint validation
- Configuration handling
"""

import pytest
from microsoft_agents.testing.scenario.external_scenario import ExternalScenario
from microsoft_agents.testing.scenario.scenario import ScenarioConfig


# =============================================================================
# ExternalScenario Initialization Tests
# =============================================================================

class TestExternalScenarioInit:
    """Test ExternalScenario initialization."""
    
    def test_init_with_endpoint(self):
        scenario = ExternalScenario(endpoint="https://example.com/api/messages")
        
        assert scenario._endpoint == "https://example.com/api/messages"
    
    def test_init_with_http_endpoint(self):
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert scenario._endpoint == "http://localhost:3978/api/messages"
    
    def test_init_with_custom_config(self):
        config = ScenarioConfig(env_file_path=".env.test", callback_server_port=9000)
        scenario = ExternalScenario(
            endpoint="https://example.com/api/messages",
            config=config
        )
        
        assert scenario._config.env_file_path == ".env.test"
        assert scenario._config.callback_server_port == 9000
    
    def test_init_with_default_config(self):
        scenario = ExternalScenario(endpoint="https://example.com/api/messages")
        
        assert scenario._config is not None
        assert scenario._config.env_file_path == ".env"


# =============================================================================
# ExternalScenario Validation Tests
# =============================================================================

class TestExternalScenarioValidation:
    """Test ExternalScenario validation."""
    
    def test_init_raises_when_endpoint_is_empty_string(self):
        with pytest.raises(ValueError) as exc_info:
            ExternalScenario(endpoint="")
        
        assert "endpoint must be provided" in str(exc_info.value)
    
    def test_init_raises_when_endpoint_is_none(self):
        with pytest.raises(ValueError) as exc_info:
            ExternalScenario(endpoint=None)
        
        assert "endpoint must be provided" in str(exc_info.value)


# =============================================================================
# ExternalScenario Inherits from Scenario Tests
# =============================================================================

class TestExternalScenarioInheritance:
    """Test that ExternalScenario properly inherits from Scenario."""
    
    def test_is_subclass_of_scenario(self):
        from microsoft_agents.testing.scenario.scenario import Scenario
        
        assert issubclass(ExternalScenario, Scenario)
    
    def test_has_run_method(self):
        scenario = ExternalScenario(endpoint="https://example.com")
        
        assert hasattr(scenario, 'run')
        assert callable(scenario.run)
    
    def test_has_client_method(self):
        scenario = ExternalScenario(endpoint="https://example.com")
        
        assert hasattr(scenario, 'client')
        assert callable(scenario.client)


# =============================================================================
# ExternalScenario Endpoint Formats Tests
# =============================================================================

class TestExternalScenarioEndpointFormats:
    """Test various endpoint formats."""
    
    def test_localhost_endpoint(self):
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        assert scenario._endpoint == "http://localhost:3978/api/messages"
    
    def test_ip_address_endpoint(self):
        scenario = ExternalScenario(endpoint="http://192.168.1.100:3978/api/messages")
        assert scenario._endpoint == "http://192.168.1.100:3978/api/messages"
    
    def test_https_endpoint(self):
        scenario = ExternalScenario(endpoint="https://my-agent.azurewebsites.net/api/messages")
        assert scenario._endpoint == "https://my-agent.azurewebsites.net/api/messages"
    
    def test_endpoint_with_port(self):
        scenario = ExternalScenario(endpoint="https://example.com:8443/api/messages")
        assert scenario._endpoint == "https://example.com:8443/api/messages"
    
    def test_endpoint_with_path(self):
        scenario = ExternalScenario(endpoint="https://example.com/v1/agents/my-agent/messages")
        assert scenario._endpoint == "https://example.com/v1/agents/my-agent/messages"


# =============================================================================
# ExternalScenario Configuration Tests
# =============================================================================

class TestExternalScenarioConfiguration:
    """Test ExternalScenario configuration handling."""
    
    def test_config_none_uses_defaults(self):
        scenario = ExternalScenario(
            endpoint="https://example.com",
            config=None
        )
        
        assert scenario._config is not None
        assert isinstance(scenario._config, ScenarioConfig)
    
    def test_config_env_file_path_is_used(self):
        config = ScenarioConfig(env_file_path="/custom/path/.env")
        scenario = ExternalScenario(
            endpoint="https://example.com",
            config=config
        )
        
        assert scenario._config.env_file_path == "/custom/path/.env"
    
    def test_config_callback_server_port_is_used(self):
        config = ScenarioConfig(callback_server_port=12345)
        scenario = ExternalScenario(
            endpoint="https://example.com",
            config=config
        )
        
        assert scenario._config.callback_server_port == 12345
