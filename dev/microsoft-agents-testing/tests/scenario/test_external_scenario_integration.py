"""Configuration tests for ExternalScenario with various configurations.

This module demonstrates different configuration patterns for ExternalScenario:
- Default configuration
- Custom response server ports
- Custom client configurations (users, headers, auth)
- Custom activity templates
- Multi-user scenarios

All tests in this module verify configuration behavior without requiring
an external agent to be running.
"""

import pytest

from microsoft_agents.testing.scenario import (
    ExternalScenario,
    ScenarioConfig,
    ClientConfig,
)
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# Test Constants
# =============================================================================

# Sample endpoint used for configuration testing (not actually connected to)
TEST_AGENT_ENDPOINT = "http://localhost:3978/api/messages"


# =============================================================================
# Configuration Variation Tests (No External Agent Required)
# =============================================================================

class TestExternalScenarioConfigurations:
    """Test different ExternalScenario configurations without running them."""
    
    def test_default_configuration(self):
        """Test ExternalScenario with default configuration."""
        scenario = ExternalScenario(endpoint=TEST_AGENT_ENDPOINT)
        
        # Verify defaults
        assert scenario._config.env_file_path == ".env"
        assert scenario._config.callback_server_port == 9378
        assert scenario._endpoint == TEST_AGENT_ENDPOINT
    
    def test_custom_env_file_configuration(self):
        """Test ExternalScenario with custom .env file path."""
        config = ScenarioConfig(env_file_path=".env.integration")
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.env_file_path == ".env.integration"
    
    def test_custom_response_port_configuration(self):
        """Test ExternalScenario with custom response server port."""
        config = ScenarioConfig(callback_server_port=9500)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.callback_server_port == 9500
    
    def test_custom_client_config_with_user(self):
        """Test ExternalScenario with pre-configured user identity."""
        client_config = ClientConfig(
            user_id="integration-test-user",
            user_name="Integration Tester"
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.client_config.user_id == "integration-test-user"
        assert scenario._config.client_config.user_name == "Integration Tester"
    
    def test_custom_client_config_with_headers(self):
        """Test ExternalScenario with custom headers."""
        client_config = ClientConfig(
            headers={
                "X-Test-Header": "test-value",
                "X-Environment": "integration"
            }
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.client_config.headers["X-Test-Header"] == "test-value"
        assert scenario._config.client_config.headers["X-Environment"] == "integration"
    
    def test_custom_client_config_with_auth_token(self):
        """Test ExternalScenario with pre-configured auth token."""
        client_config = ClientConfig(auth_token="pre-generated-jwt-token")
        config = ScenarioConfig(client_config=client_config)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.client_config.auth_token == "pre-generated-jwt-token"
    
    def test_custom_activity_template(self):
        """Test ExternalScenario with custom activity template."""
        template = ActivityTemplate(
            channel_id="integration-test",
            locale="en-US",
        )
        config = ScenarioConfig(activity_template=template)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.activity_template is template
    
    def test_full_custom_configuration(self):
        """Test ExternalScenario with fully customized configuration."""
        client_config = ClientConfig(
            user_id="power-user",
            user_name="Power User",
            headers={"X-Priority": "high"},
            auth_token="custom-token"
        )
        template = ActivityTemplate(
            channel_id="custom-channel",
            locale="en-GB",
        )
        config = ScenarioConfig(
            env_file_path=".env.custom",
            callback_server_port=9999,
            client_config=client_config,
            activity_template=template,
        )
        scenario = ExternalScenario(
            endpoint="https://custom-agent.example.com/api/messages",
            config=config
        )
        
        assert scenario._endpoint == "https://custom-agent.example.com/api/messages"
        assert scenario._config.env_file_path == ".env.custom"
        assert scenario._config.callback_server_port == 9999
        assert scenario._config.client_config.user_id == "power-user"
        assert scenario._config.client_config.headers["X-Priority"] == "high"


# =============================================================================
# Different Endpoint Patterns
# =============================================================================

class TestExternalScenarioEndpointPatterns:
    """Test various endpoint URL patterns."""
    
    def test_localhost_http_endpoint(self):
        """Test with localhost HTTP endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        assert "localhost" in scenario._endpoint
        assert "http://" in scenario._endpoint
    
    def test_localhost_https_endpoint(self):
        """Test with localhost HTTPS endpoint."""
        scenario = ExternalScenario(endpoint="https://localhost:3978/api/messages")
        assert "https://" in scenario._endpoint
    
    def test_azure_endpoint(self):
        """Test with Azure-hosted endpoint."""
        scenario = ExternalScenario(
            endpoint="https://my-agent.azurewebsites.net/api/messages"
        )
        assert "azurewebsites.net" in scenario._endpoint
    
    def test_custom_domain_endpoint(self):
        """Test with custom domain endpoint."""
        scenario = ExternalScenario(
            endpoint="https://agents.mycompany.com/v1/bot/messages"
        )
        assert "mycompany.com" in scenario._endpoint
    
    def test_endpoint_with_custom_path(self):
        """Test with non-standard API path."""
        scenario = ExternalScenario(
            endpoint="https://example.com/bots/production/v2/messages"
        )
        assert "/bots/production/v2/messages" in scenario._endpoint


# =============================================================================
# Multi-User Configuration Patterns
# =============================================================================

class TestExternalScenarioMultiUserPatterns:
    """Test configurations for multi-user scenarios."""
    
    def test_default_user_configuration(self):
        """Test default user configuration."""
        scenario = ExternalScenario(endpoint=TEST_AGENT_ENDPOINT)
        
        assert scenario._config.client_config.user_id == "user-id"
        assert scenario._config.client_config.user_name == "User"
    
    def test_alice_user_configuration(self):
        """Test configuration for user 'Alice'."""
        alice_config = ClientConfig(user_id="alice-123", user_name="Alice")
        config = ScenarioConfig(client_config=alice_config)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.client_config.user_id == "alice-123"
        assert scenario._config.client_config.user_name == "Alice"
    
    def test_bob_user_configuration(self):
        """Test configuration for user 'Bob'."""
        bob_config = ClientConfig(user_id="bob-456", user_name="Bob")
        config = ScenarioConfig(client_config=bob_config)
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=config
        )
        
        assert scenario._config.client_config.user_id == "bob-456"
        assert scenario._config.client_config.user_name == "Bob"
    
    def test_creating_user_configs_for_multi_user_test(self):
        """Demonstrate creating multiple user configs for a single scenario."""
        # Base scenario with default user
        base_config = ScenarioConfig(
            callback_server_port=9400,
        )
        scenario = ExternalScenario(
            endpoint=TEST_AGENT_ENDPOINT,
            config=base_config
        )
        
        # Create user configs that can be passed to factory.create_client()
        alice = ClientConfig().with_user("alice", "Alice Smith")
        bob = ClientConfig().with_user("bob", "Bob Jones")
        charlie = ClientConfig().with_user("charlie", "Charlie Brown")
        
        # Verify each user config is different
        assert alice.user_id != bob.user_id
        assert bob.user_id != charlie.user_id
        assert alice.user_name == "Alice Smith"
        assert bob.user_name == "Bob Jones"
        assert charlie.user_name == "Charlie Brown"
