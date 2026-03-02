# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ClientConfig and ScenarioConfig classes."""

import pytest

from microsoft_agents.testing.core.config import ClientConfig, ScenarioConfig
from microsoft_agents.testing.core.fluent import ActivityTemplate


# ============================================================================
# ClientConfig Initialization Tests
# ============================================================================

class TestClientConfigInitialization:
    """Tests for ClientConfig initialization."""

    def test_default_initialization(self):
        """ClientConfig initializes with default values."""
        config = ClientConfig()
        
        assert config.headers == {}
        assert config.auth_token is None
        assert config.activity_template is None

    def test_initialization_with_headers(self):
        """ClientConfig initializes with custom headers."""
        headers = {"X-Custom-Header": "value", "Accept": "application/json"}
        config = ClientConfig(headers=headers)
        
        assert config.headers == headers

    def test_initialization_with_auth_token(self):
        """ClientConfig initializes with auth token."""
        config = ClientConfig(auth_token="my-token-123")
        
        assert config.auth_token == "my-token-123"

    def test_initialization_with_activity_template(self):
        """ClientConfig initializes with activity template."""
        template = ActivityTemplate(text="Hello")
        config = ClientConfig(activity_template=template)
        
        assert config.activity_template is template

    def test_initialization_with_all_parameters(self):
        """ClientConfig initializes with all parameters."""
        headers = {"X-Custom": "value"}
        template = ActivityTemplate(text="Test")
        
        config = ClientConfig(
            headers=headers,
            auth_token="token-abc",
            activity_template=template,
        )
        
        assert config.headers == headers
        assert config.auth_token == "token-abc"
        assert config.activity_template is template


# ============================================================================
# ClientConfig with_headers Tests
# ============================================================================

class TestClientConfigWithHeaders:
    """Tests for ClientConfig.with_headers method."""

    def test_with_headers_adds_new_headers(self):
        """with_headers adds new headers to an empty config."""
        config = ClientConfig()
        
        new_config = config.with_headers(
            Authorization="Bearer token",
            ContentType="application/json"
        )
        
        assert new_config.headers == {
            "Authorization": "Bearer token",
            "ContentType": "application/json",
        }

    def test_with_headers_merges_existing_headers(self):
        """with_headers merges with existing headers."""
        config = ClientConfig(headers={"Existing": "header"})
        
        new_config = config.with_headers(New="value")
        
        assert new_config.headers == {"Existing": "header", "New": "value"}

    def test_with_headers_overwrites_duplicate_keys(self):
        """with_headers overwrites duplicate header keys."""
        config = ClientConfig(headers={"Key": "old-value"})
        
        new_config = config.with_headers(Key="new-value")
        
        assert new_config.headers == {"Key": "new-value"}

    def test_with_headers_returns_new_instance(self):
        """with_headers returns a new ClientConfig instance."""
        config = ClientConfig()
        
        new_config = config.with_headers(Header="value")
        
        assert new_config is not config
        assert config.headers == {}  # Original unchanged

    def test_with_headers_preserves_auth_token(self):
        """with_headers preserves the auth_token."""
        config = ClientConfig(auth_token="my-token")
        
        new_config = config.with_headers(Header="value")
        
        assert new_config.auth_token == "my-token"

    def test_with_headers_preserves_activity_template(self):
        """with_headers preserves the activity_template."""
        template = ActivityTemplate(text="Test")
        config = ClientConfig(activity_template=template)
        
        new_config = config.with_headers(Header="value")
        
        assert new_config.activity_template is template


# ============================================================================
# ClientConfig with_auth_token Tests
# ============================================================================

class TestClientConfigWithAuthToken:
    """Tests for ClientConfig.with_auth_token method."""

    def test_with_auth_token_sets_token(self):
        """with_auth_token sets the auth token."""
        config = ClientConfig()
        
        new_config = config.with_auth_token("new-token")
        
        assert new_config.auth_token == "new-token"

    def test_with_auth_token_replaces_existing_token(self):
        """with_auth_token replaces existing token."""
        config = ClientConfig(auth_token="old-token")
        
        new_config = config.with_auth_token("new-token")
        
        assert new_config.auth_token == "new-token"

    def test_with_auth_token_returns_new_instance(self):
        """with_auth_token returns a new ClientConfig instance."""
        config = ClientConfig(auth_token="original")
        
        new_config = config.with_auth_token("changed")
        
        assert new_config is not config
        assert config.auth_token == "original"  # Original unchanged

    def test_with_auth_token_preserves_headers(self):
        """with_auth_token preserves headers."""
        config = ClientConfig(headers={"Key": "value"})
        
        new_config = config.with_auth_token("token")
        
        assert new_config.headers == {"Key": "value"}

    def test_with_auth_token_preserves_activity_template(self):
        """with_auth_token preserves activity_template."""
        template = ActivityTemplate(text="Test")
        config = ClientConfig(activity_template=template)
        
        new_config = config.with_auth_token("token")
        
        assert new_config.activity_template is template


# ============================================================================
# ClientConfig with_template Tests
# ============================================================================

class TestClientConfigWithTemplate:
    """Tests for ClientConfig.with_template method."""

    def test_with_template_sets_template(self):
        """with_template sets the activity template."""
        config = ClientConfig()
        template = ActivityTemplate(text="Hello")
        
        new_config = config.with_template(template)
        
        assert new_config.activity_template is template

    def test_with_template_replaces_existing_template(self):
        """with_template replaces existing template."""
        old_template = ActivityTemplate(text="Old")
        new_template = ActivityTemplate(text="New")
        config = ClientConfig(activity_template=old_template)
        
        new_config = config.with_template(new_template)
        
        assert new_config.activity_template is new_template

    def test_with_template_returns_new_instance(self):
        """with_template returns a new ClientConfig instance."""
        config = ClientConfig()
        template = ActivityTemplate(text="Test")
        
        new_config = config.with_template(template)
        
        assert new_config is not config

    def test_with_template_preserves_headers(self):
        """with_template preserves headers."""
        config = ClientConfig(headers={"Key": "value"})
        template = ActivityTemplate(text="Test")
        
        new_config = config.with_template(template)
        
        assert new_config.headers == {"Key": "value"}

    def test_with_template_preserves_auth_token(self):
        """with_template preserves auth_token."""
        config = ClientConfig(auth_token="my-token")
        template = ActivityTemplate(text="Test")
        
        new_config = config.with_template(template)
        
        assert new_config.auth_token == "my-token"


# ============================================================================
# ClientConfig Method Chaining Tests
# ============================================================================

class TestClientConfigChaining:
    """Tests for chaining ClientConfig methods."""

    def test_chaining_multiple_methods(self):
        """Multiple with_* methods can be chained."""
        template = ActivityTemplate(text="Test")
        
        config = (
            ClientConfig()
            .with_headers(Header1="value1")
            .with_auth_token("my-token")
            .with_template(template)
            .with_headers(Header2="value2")
        )
        
        assert config.headers == {"Header1": "value1", "Header2": "value2"}
        assert config.auth_token == "my-token"
        assert config.activity_template is template


# ============================================================================
# ScenarioConfig Initialization Tests
# ============================================================================

class TestScenarioConfigInitialization:
    """Tests for ScenarioConfig initialization."""

    def test_default_initialization(self):
        """ScenarioConfig initializes with default values."""
        config = ScenarioConfig()
        
        assert config.env_file_path is None
        assert config.callback_server_port == 9378
        assert isinstance(config.client_config, ClientConfig)

    def test_initialization_with_env_file_path(self):
        """ScenarioConfig initializes with env_file_path."""
        config = ScenarioConfig(env_file_path="/path/to/.env")
        
        assert config.env_file_path == "/path/to/.env"

    def test_initialization_with_custom_port(self):
        """ScenarioConfig initializes with custom callback_server_port."""
        config = ScenarioConfig(callback_server_port=8080)
        
        assert config.callback_server_port == 8080

    def test_initialization_with_client_config(self):
        """ScenarioConfig initializes with custom client_config."""
        client_config = ClientConfig(auth_token="test-token")
        config = ScenarioConfig(client_config=client_config)
        
        assert config.client_config is client_config
        assert config.client_config.auth_token == "test-token"

    def test_initialization_with_all_parameters(self):
        """ScenarioConfig initializes with all parameters."""
        client_config = ClientConfig(headers={"Key": "value"})
        
        config = ScenarioConfig(
            env_file_path="./config.env",
            callback_server_port=3000,
            client_config=client_config,
        )
        
        assert config.env_file_path == "./config.env"
        assert config.callback_server_port == 3000
        assert config.client_config is client_config


# ============================================================================
# ScenarioConfig Default ClientConfig Tests
# ============================================================================

class TestScenarioConfigDefaultClientConfig:
    """Tests for ScenarioConfig's default ClientConfig behavior."""

    def test_default_client_config_is_empty(self):
        """Default client_config has default values."""
        config = ScenarioConfig()
        
        assert config.client_config.headers == {}
        assert config.client_config.auth_token is None
        assert config.client_config.activity_template is None

    def test_multiple_scenario_configs_have_independent_client_configs(self):
        """Each ScenarioConfig instance has its own ClientConfig."""
        config1 = ScenarioConfig()
        config2 = ScenarioConfig()
        
        # Modify one doesn't affect the other (default_factory creates new instances)
        assert config1.client_config is not config2.client_config


# ============================================================================
# ClientConfig Dataclass Features Tests
# ============================================================================

class TestClientConfigDataclassFeatures:
    """Tests for ClientConfig dataclass behavior."""

    def test_equality_same_values(self):
        """ClientConfig instances with same values are equal."""
        config1 = ClientConfig(headers={"Key": "value"}, auth_token="token")
        config2 = ClientConfig(headers={"Key": "value"}, auth_token="token")
        
        assert config1 == config2

    def test_equality_different_headers(self):
        """ClientConfig instances with different headers are not equal."""
        config1 = ClientConfig(headers={"Key": "value1"})
        config2 = ClientConfig(headers={"Key": "value2"})
        
        assert config1 != config2

    def test_equality_different_auth_token(self):
        """ClientConfig instances with different auth_token are not equal."""
        config1 = ClientConfig(auth_token="token1")
        config2 = ClientConfig(auth_token="token2")
        
        assert config1 != config2


# ============================================================================
# ScenarioConfig Dataclass Features Tests
# ============================================================================

class TestScenarioConfigDataclassFeatures:
    """Tests for ScenarioConfig dataclass behavior."""

    def test_equality_same_values(self):
        """ScenarioConfig instances with same values are equal."""
        client_config = ClientConfig(auth_token="token")
        config1 = ScenarioConfig(
            env_file_path="/path",
            callback_server_port=8080,
            client_config=client_config,
        )
        config2 = ScenarioConfig(
            env_file_path="/path",
            callback_server_port=8080,
            client_config=client_config,
        )
        
        assert config1 == config2

    def test_equality_different_port(self):
        """ScenarioConfig instances with different ports are not equal."""
        config1 = ScenarioConfig(callback_server_port=8080)
        config2 = ScenarioConfig(callback_server_port=9090)
        
        assert config1 != config2
