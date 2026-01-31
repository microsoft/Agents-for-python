# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ClientConfig class."""

import pytest

from microsoft_agents.testing.core.client_config import ClientConfig
from microsoft_agents.testing.core.fluent import ActivityTemplate


class TestClientConfigInitialization:
    """Tests for ClientConfig initialization."""

    def test_default_initialization(self):
        """ClientConfig should initialize with default values."""
        config = ClientConfig()
        
        assert config.headers == {}
        assert config.auth_token is None
        assert config.activity_template is None
        assert config.user_id == "user-id"
        assert config.user_name == "User"

    def test_initialization_with_custom_values(self):
        """ClientConfig should initialize with custom values."""
        template = ActivityTemplate(type="message")
        config = ClientConfig(
            headers={"Authorization": "Bearer token"},
            auth_token="my-token",
            activity_template=template,
            user_id="custom-user",
            user_name="Custom User",
        )
        
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.auth_token == "my-token"
        assert config.activity_template == template
        assert config.user_id == "custom-user"
        assert config.user_name == "Custom User"


class TestClientConfigWithHeaders:
    """Tests for the with_headers() method."""

    def test_with_headers_returns_new_config(self):
        """with_headers() should return a new config instance."""
        config = ClientConfig()
        new_config = config.with_headers(Authorization="Bearer token")
        
        assert new_config is not config

    def test_with_headers_adds_headers(self):
        """with_headers() should add the specified headers."""
        config = ClientConfig()
        new_config = config.with_headers(
            Authorization="Bearer token",
            ContentType="application/json"
        )
        
        assert new_config.headers == {
            "Authorization": "Bearer token",
            "ContentType": "application/json"
        }

    def test_with_headers_merges_existing_headers(self):
        """with_headers() should merge with existing headers."""
        config = ClientConfig(headers={"Existing": "header"})
        new_config = config.with_headers(New="value")
        
        assert new_config.headers == {
            "Existing": "header",
            "New": "value"
        }

    def test_with_headers_preserves_other_properties(self):
        """with_headers() should preserve other config properties."""
        config = ClientConfig(
            auth_token="my-token",
            user_id="my-user",
            user_name="My User"
        )
        new_config = config.with_headers(Header="value")
        
        assert new_config.auth_token == "my-token"
        assert new_config.user_id == "my-user"
        assert new_config.user_name == "My User"


class TestClientConfigWithAuth:
    """Tests for the with_auth() method."""

    def test_with_auth_returns_new_config(self):
        """with_auth() should return a new config instance."""
        config = ClientConfig()
        new_config = config.with_auth("new-token")
        
        assert new_config is not config

    def test_with_auth_sets_token(self):
        """with_auth() should set the auth token."""
        config = ClientConfig()
        new_config = config.with_auth("my-auth-token")
        
        assert new_config.auth_token == "my-auth-token"

    def test_with_auth_replaces_existing_token(self):
        """with_auth() should replace an existing token."""
        config = ClientConfig(auth_token="old-token")
        new_config = config.with_auth("new-token")
        
        assert new_config.auth_token == "new-token"

    def test_with_auth_preserves_other_properties(self):
        """with_auth() should preserve other config properties."""
        config = ClientConfig(
            headers={"Header": "value"},
            user_id="my-user",
            user_name="My User"
        )
        new_config = config.with_auth("token")
        
        assert new_config.headers == {"Header": "value"}
        assert new_config.user_id == "my-user"
        assert new_config.user_name == "My User"


class TestClientConfigWithUser:
    """Tests for the with_user() method."""

    def test_with_user_returns_new_config(self):
        """with_user() should return a new config instance."""
        config = ClientConfig()
        new_config = config.with_user("new-user")
        
        assert new_config is not config

    def test_with_user_sets_user_id_and_name(self):
        """with_user() should set user_id and user_name."""
        config = ClientConfig()
        new_config = config.with_user("new-user", "New User Name")
        
        assert new_config.user_id == "new-user"
        assert new_config.user_name == "New User Name"

    def test_with_user_defaults_name_to_id(self):
        """with_user() should default user_name to user_id if not provided."""
        config = ClientConfig()
        new_config = config.with_user("just-user-id")
        
        assert new_config.user_id == "just-user-id"
        assert new_config.user_name == "just-user-id"

    def test_with_user_preserves_other_properties(self):
        """with_user() should preserve other config properties."""
        config = ClientConfig(
            headers={"Header": "value"},
            auth_token="my-token"
        )
        new_config = config.with_user("new-user", "New User")
        
        assert new_config.headers == {"Header": "value"}
        assert new_config.auth_token == "my-token"


class TestClientConfigWithTemplate:
    """Tests for the with_template() method."""

    def test_with_template_returns_new_config(self):
        """with_template() should return a new config instance."""
        config = ClientConfig()
        template = ActivityTemplate(type="message")
        new_config = config.with_template(template)
        
        assert new_config is not config

    def test_with_template_sets_template(self):
        """with_template() should set the activity template."""
        config = ClientConfig()
        template = ActivityTemplate(type="message", text="Hello")
        new_config = config.with_template(template)
        
        assert new_config.activity_template == template

    def test_with_template_replaces_existing_template(self):
        """with_template() should replace an existing template."""
        old_template = ActivityTemplate(type="typing")
        new_template = ActivityTemplate(type="message")
        config = ClientConfig(activity_template=old_template)
        new_config = config.with_template(new_template)
        
        assert new_config.activity_template == new_template

    def test_with_template_preserves_other_properties(self):
        """with_template() should preserve other config properties."""
        config = ClientConfig(
            headers={"Header": "value"},
            auth_token="my-token",
            user_id="my-user"
        )
        template = ActivityTemplate(type="message")
        new_config = config.with_template(template)
        
        assert new_config.headers == {"Header": "value"}
        assert new_config.auth_token == "my-token"
        assert new_config.user_id == "my-user"


class TestClientConfigChaining:
    """Tests for chaining configuration methods."""

    def test_chain_multiple_methods(self):
        """Configuration methods can be chained together."""
        template = ActivityTemplate(type="message")
        config = (
            ClientConfig()
            .with_headers(Authorization="Bearer token")
            .with_auth("my-token")
            .with_user("user-123", "Test User")
            .with_template(template)
        )
        
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.auth_token == "my-token"
        assert config.user_id == "user-123"
        assert config.user_name == "Test User"
        assert config.activity_template == template

    def test_original_config_unchanged_after_chaining(self):
        """Original config should remain unchanged after chaining."""
        original = ClientConfig()
        _ = (
            original
            .with_headers(Header="value")
            .with_auth("token")
            .with_user("user", "User Name")
        )
        
        assert original.headers == {}
        assert original.auth_token is None
        assert original.user_id == "user-id"
        assert original.user_name == "User"
