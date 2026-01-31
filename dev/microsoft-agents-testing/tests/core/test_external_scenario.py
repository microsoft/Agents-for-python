# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ExternalScenario class."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from microsoft_agents.testing.core.external_scenario import ExternalScenario
from microsoft_agents.testing.core.scenario import ScenarioConfig
from microsoft_agents.testing.core.client_config import ClientConfig
from microsoft_agents.testing.core.fluent import ActivityTemplate


# ============================================================================
# ExternalScenario Initialization Tests
# ============================================================================

class TestExternalScenarioInitialization:
    """Tests for ExternalScenario initialization."""

    def test_requires_endpoint(self):
        """ExternalScenario requires a non-empty endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint="")

    def test_requires_endpoint_not_none(self):
        """ExternalScenario raises for None endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint=None)

    def test_stores_endpoint(self):
        """ExternalScenario stores the provided endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert scenario._endpoint == "http://localhost:3978"

    def test_stores_endpoint_with_path(self):
        """ExternalScenario stores endpoint with path."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        
        assert scenario._endpoint == "http://localhost:3978/api/messages"

    def test_uses_default_config(self):
        """ExternalScenario uses default config when none provided."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert isinstance(scenario._config, ScenarioConfig)
        assert scenario._config.env_file_path == ".env"
        assert scenario._config.callback_server_port == 9378

    def test_accepts_custom_config(self):
        """ExternalScenario accepts custom ScenarioConfig."""
        custom_config = ScenarioConfig(
            env_file_path=".env.test",
            callback_server_port=8080,
        )
        scenario = ExternalScenario(
            endpoint="http://localhost:3978",
            config=custom_config
        )
        
        assert scenario._config is custom_config
        assert scenario._config.env_file_path == ".env.test"
        assert scenario._config.callback_server_port == 8080

    def test_inherits_from_scenario(self):
        """ExternalScenario inherits from Scenario base class."""
        from microsoft_agents.testing.core.scenario import Scenario
        
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert isinstance(scenario, Scenario)


# ============================================================================
# ExternalScenario Configuration Tests
# ============================================================================

class TestExternalScenarioConfiguration:
    """Tests for ExternalScenario with various configurations."""

    def test_with_custom_env_file(self):
        """ExternalScenario with custom env file path."""
        config = ScenarioConfig(env_file_path="/path/to/custom/.env")
        scenario = ExternalScenario(
            endpoint="http://agent.example.com",
            config=config
        )
        
        assert scenario._config.env_file_path == "/path/to/custom/.env"

    def test_with_custom_port(self):
        """ExternalScenario with custom callback server port."""
        config = ScenarioConfig(callback_server_port=9999)
        scenario = ExternalScenario(
            endpoint="http://agent.example.com",
            config=config
        )
        
        assert scenario._config.callback_server_port == 9999

    def test_with_custom_activity_template(self):
        """ExternalScenario with custom activity template."""
        template = ActivityTemplate(
            channel_id="custom-channel",
            locale="de-DE",
        )
        config = ScenarioConfig(activity_template=template)
        scenario = ExternalScenario(
            endpoint="http://agent.example.com",
            config=config
        )
        
        assert scenario._config.activity_template is template

    def test_with_custom_client_config(self):
        """ExternalScenario with custom client config."""
        client_config = ClientConfig(
            user_id="custom-user",
            user_name="Custom User",
            auth_token="test-token",
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint="http://agent.example.com",
            config=config
        )
        
        assert scenario._config.client_config is client_config

    def test_with_all_custom_settings(self):
        """ExternalScenario with all custom configuration."""
        template = ActivityTemplate(channel_id="full-custom")
        client_config = ClientConfig(user_id="full-custom-user")
        
        config = ScenarioConfig(
            env_file_path=".env.production",
            callback_server_port=5000,
            activity_template=template,
            client_config=client_config,
        )
        scenario = ExternalScenario(
            endpoint="https://production-agent.example.com",
            config=config
        )
        
        assert scenario._endpoint == "https://production-agent.example.com"
        assert scenario._config.env_file_path == ".env.production"
        assert scenario._config.callback_server_port == 5000
        assert scenario._config.activity_template is template
        assert scenario._config.client_config is client_config


# ============================================================================
# ExternalScenario Endpoint Validation Tests
# ============================================================================

class TestExternalScenarioEndpointValidation:
    """Tests for endpoint validation in ExternalScenario."""

    def test_accepts_http_endpoint(self):
        """ExternalScenario accepts http:// endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        assert scenario._endpoint == "http://localhost:3978"

    def test_accepts_https_endpoint(self):
        """ExternalScenario accepts https:// endpoint."""
        scenario = ExternalScenario(endpoint="https://secure-agent.example.com")
        assert scenario._endpoint == "https://secure-agent.example.com"

    def test_accepts_endpoint_with_port(self):
        """ExternalScenario accepts endpoint with port."""
        scenario = ExternalScenario(endpoint="http://localhost:8080")
        assert scenario._endpoint == "http://localhost:8080"

    def test_accepts_endpoint_with_path(self):
        """ExternalScenario accepts endpoint with path."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/v1")
        assert scenario._endpoint == "http://localhost:3978/api/v1"

    def test_accepts_ip_address_endpoint(self):
        """ExternalScenario accepts IP address endpoint."""
        scenario = ExternalScenario(endpoint="http://192.168.1.100:3978")
        assert scenario._endpoint == "http://192.168.1.100:3978"

    def test_rejects_empty_string(self):
        """ExternalScenario rejects empty string endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint="")


# ============================================================================
# ExternalScenario Run Method Tests (with mocking)
# ============================================================================

class TestExternalScenarioRun:
    """Tests for ExternalScenario.run() method behavior."""

    def test_has_run_method(self):
        """ExternalScenario has run method."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert hasattr(scenario, 'run')
        assert callable(scenario.run)

    def test_has_client_method(self):
        """ExternalScenario inherits client convenience method."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert hasattr(scenario, 'client')
        assert callable(scenario.client)


# ============================================================================
# ExternalScenario Multiple Instances Tests
# ============================================================================

class TestExternalScenarioMultipleInstances:
    """Tests for multiple ExternalScenario instances."""

    def test_independent_instances(self):
        """Multiple ExternalScenario instances are independent."""
        scenario1 = ExternalScenario(endpoint="http://agent1.example.com")
        scenario2 = ExternalScenario(endpoint="http://agent2.example.com")
        
        assert scenario1._endpoint != scenario2._endpoint
        assert scenario1._config is not scenario2._config

    def test_instances_with_different_configs(self):
        """Multiple instances can have different configs."""
        config1 = ScenarioConfig(callback_server_port=9001)
        config2 = ScenarioConfig(callback_server_port=9002)
        
        scenario1 = ExternalScenario(endpoint="http://agent1.example.com", config=config1)
        scenario2 = ExternalScenario(endpoint="http://agent2.example.com", config=config2)
        
        assert scenario1._config.callback_server_port == 9001
        assert scenario2._config.callback_server_port == 9002

    def test_instances_share_config_reference_if_same(self):
        """Instances can share config if explicitly provided."""
        shared_config = ScenarioConfig(callback_server_port=7777)
        
        scenario1 = ExternalScenario(endpoint="http://agent1.example.com", config=shared_config)
        scenario2 = ExternalScenario(endpoint="http://agent2.example.com", config=shared_config)
        
        assert scenario1._config is scenario2._config


# ============================================================================
# ExternalScenario Type Checking Tests
# ============================================================================

class TestExternalScenarioTypeChecking:
    """Tests for ExternalScenario type annotations and protocol compliance."""

    def test_config_type(self):
        """_config is ScenarioConfig."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert isinstance(scenario._config, ScenarioConfig)

    def test_endpoint_type(self):
        """_endpoint is a string."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        
        assert isinstance(scenario._endpoint, str)
