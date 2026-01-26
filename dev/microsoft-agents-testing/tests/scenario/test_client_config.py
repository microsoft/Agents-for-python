"""
Unit tests for the ClientConfig class.

This module tests:
- ClientConfig initialization and default values
- Immutable builder methods (with_headers, with_auth, with_user, with_template)
- Chaining of builder methods
"""

import pytest
from microsoft_agents.testing.scenario.client_config import ClientConfig
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# ClientConfig Initialization Tests
# =============================================================================

class TestClientConfigInit:
    """Test ClientConfig initialization and defaults."""
    
    def test_default_initialization(self):
        config = ClientConfig()
        
        assert config.headers == {}
        assert config.auth_token is None
        assert config.activity_template is None
        assert config.user_id == "user-id"
        assert config.user_name == "User"
    
    def test_init_with_custom_headers(self):
        headers = {"X-Custom": "value", "X-Another": "test"}
        config = ClientConfig(headers=headers)
        
        assert config.headers == headers
    
    def test_init_with_auth_token(self):
        config = ClientConfig(auth_token="my-token-123")
        
        assert config.auth_token == "my-token-123"
    
    def test_init_with_custom_user(self):
        config = ClientConfig(user_id="alice", user_name="Alice Smith")
        
        assert config.user_id == "alice"
        assert config.user_name == "Alice Smith"
    
    def test_init_with_activity_template(self):
        template = ActivityTemplate()
        config = ClientConfig(activity_template=template)
        
        assert config.activity_template is template


# =============================================================================
# with_headers Tests
# =============================================================================

class TestClientConfigWithHeaders:
    """Test the with_headers method."""
    
    def test_with_headers_returns_new_instance(self):
        original = ClientConfig()
        new_config = original.with_headers(Authorization="Bearer token")
        
        assert new_config is not original
    
    def test_with_headers_adds_headers(self):
        original = ClientConfig()
        new_config = original.with_headers(
            Authorization="Bearer token",
            **{"X-Custom-Header": "value"}
        )
        
        assert new_config.headers == {
            "Authorization": "Bearer token",
            "X-Custom-Header": "value"
        }
    
    def test_with_headers_preserves_existing_headers(self):
        original = ClientConfig(headers={"X-Existing": "existing"})
        new_config = original.with_headers(**{"X-New": "new"})
        
        assert new_config.headers == {
            "X-Existing": "existing",
            "X-New": "new"
        }
    
    def test_with_headers_can_override_existing(self):
        original = ClientConfig(headers={"X-Header": "old"})
        new_config = original.with_headers(**{"X-Header": "new"})
        
        assert new_config.headers["X-Header"] == "new"
    
    def test_original_headers_unchanged_after_with_headers(self):
        original = ClientConfig(headers={"X-Original": "value"})
        _ = original.with_headers(**{"X-New": "new"})
        
        assert "X-New" not in original.headers
        assert original.headers == {"X-Original": "value"}
    
    def test_with_headers_preserves_other_fields(self):
        original = ClientConfig(
            auth_token="token",
            user_id="alice",
            user_name="Alice"
        )
        new_config = original.with_headers(**{"X-Custom": "value"})
        
        assert new_config.auth_token == "token"
        assert new_config.user_id == "alice"
        assert new_config.user_name == "Alice"


# =============================================================================
# with_auth Tests
# =============================================================================

class TestClientConfigWithAuth:
    """Test the with_auth method."""
    
    def test_with_auth_returns_new_instance(self):
        original = ClientConfig()
        new_config = original.with_auth("new-token")
        
        assert new_config is not original
    
    def test_with_auth_sets_token(self):
        original = ClientConfig()
        new_config = original.with_auth("my-auth-token")
        
        assert new_config.auth_token == "my-auth-token"
    
    def test_with_auth_replaces_existing_token(self):
        original = ClientConfig(auth_token="old-token")
        new_config = original.with_auth("new-token")
        
        assert new_config.auth_token == "new-token"
    
    def test_original_token_unchanged_after_with_auth(self):
        original = ClientConfig(auth_token="original-token")
        _ = original.with_auth("modified-token")
        
        assert original.auth_token == "original-token"
    
    def test_with_auth_preserves_other_fields(self):
        original = ClientConfig(
            headers={"X-Header": "value"},
            user_id="bob",
            user_name="Bob"
        )
        new_config = original.with_auth("token")
        
        assert new_config.headers == {"X-Header": "value"}
        assert new_config.user_id == "bob"
        assert new_config.user_name == "Bob"


# =============================================================================
# with_user Tests
# =============================================================================

class TestClientConfigWithUser:
    """Test the with_user method."""
    
    def test_with_user_returns_new_instance(self):
        original = ClientConfig()
        new_config = original.with_user("alice")
        
        assert new_config is not original
    
    def test_with_user_sets_user_id(self):
        original = ClientConfig()
        new_config = original.with_user("alice")
        
        assert new_config.user_id == "alice"
    
    def test_with_user_uses_user_id_as_default_name(self):
        original = ClientConfig()
        new_config = original.with_user("alice")
        
        assert new_config.user_name == "alice"
    
    def test_with_user_sets_custom_user_name(self):
        original = ClientConfig()
        new_config = original.with_user("alice", "Alice Smith")
        
        assert new_config.user_id == "alice"
        assert new_config.user_name == "Alice Smith"
    
    def test_with_user_replaces_existing_user(self):
        original = ClientConfig(user_id="bob", user_name="Bob")
        new_config = original.with_user("alice", "Alice")
        
        assert new_config.user_id == "alice"
        assert new_config.user_name == "Alice"
    
    def test_original_user_unchanged_after_with_user(self):
        original = ClientConfig(user_id="original", user_name="Original")
        _ = original.with_user("modified", "Modified")
        
        assert original.user_id == "original"
        assert original.user_name == "Original"
    
    def test_with_user_preserves_other_fields(self):
        original = ClientConfig(
            headers={"X-Header": "value"},
            auth_token="token"
        )
        new_config = original.with_user("alice", "Alice")
        
        assert new_config.headers == {"X-Header": "value"}
        assert new_config.auth_token == "token"


# =============================================================================
# with_template Tests
# =============================================================================

class TestClientConfigWithTemplate:
    """Test the with_template method."""
    
    def test_with_template_returns_new_instance(self):
        original = ClientConfig()
        template = ActivityTemplate()
        new_config = original.with_template(template)
        
        assert new_config is not original
    
    def test_with_template_sets_template(self):
        original = ClientConfig()
        template = ActivityTemplate()
        new_config = original.with_template(template)
        
        assert new_config.activity_template is template
    
    def test_with_template_replaces_existing_template(self):
        old_template = ActivityTemplate()
        new_template = ActivityTemplate()
        original = ClientConfig(activity_template=old_template)
        new_config = original.with_template(new_template)
        
        assert new_config.activity_template is new_template
        assert new_config.activity_template is not old_template
    
    def test_original_template_unchanged_after_with_template(self):
        original_template = ActivityTemplate()
        original = ClientConfig(activity_template=original_template)
        new_template = ActivityTemplate()
        _ = original.with_template(new_template)
        
        assert original.activity_template is original_template
    
    def test_with_template_preserves_other_fields(self):
        original = ClientConfig(
            headers={"X-Header": "value"},
            auth_token="token",
            user_id="alice",
            user_name="Alice"
        )
        template = ActivityTemplate()
        new_config = original.with_template(template)
        
        assert new_config.headers == {"X-Header": "value"}
        assert new_config.auth_token == "token"
        assert new_config.user_id == "alice"
        assert new_config.user_name == "Alice"


# =============================================================================
# Method Chaining Tests
# =============================================================================

class TestClientConfigChaining:
    """Test chaining of builder methods."""
    
    def test_chain_all_methods(self):
        template = ActivityTemplate()
        config = (
            ClientConfig()
            .with_headers(**{"X-Custom": "value"})
            .with_auth("my-token")
            .with_user("alice", "Alice Smith")
            .with_template(template)
        )
        
        assert config.headers == {"X-Custom": "value"}
        assert config.auth_token == "my-token"
        assert config.user_id == "alice"
        assert config.user_name == "Alice Smith"
        assert config.activity_template is template
    
    def test_chain_with_headers_multiple_times(self):
        config = (
            ClientConfig()
            .with_headers(**{"X-First": "first"})
            .with_headers(**{"X-Second": "second"})
        )
        
        assert config.headers == {"X-First": "first", "X-Second": "second"}
    
    def test_chain_preserves_immutability(self):
        original = ClientConfig()
        step1 = original.with_auth("token1")
        step2 = step1.with_user("alice")
        step3 = step2.with_headers(**{"X-Header": "value"})
        
        # Each step should be independent
        assert original.auth_token is None
        assert step1.user_id == "user-id"
        assert step2.headers == {}
        
        # Final config should have all values
        assert step3.auth_token == "token1"
        assert step3.user_id == "alice"
        assert step3.headers == {"X-Header": "value"}


# =============================================================================
# Edge Cases
# =============================================================================

class TestClientConfigEdgeCases:
    """Test edge cases for ClientConfig."""
    
    def test_with_user_empty_name_uses_user_id(self):
        config = ClientConfig().with_user("user123", None)
        
        assert config.user_id == "user123"
        assert config.user_name == "user123"
    
    def test_with_headers_empty_dict(self):
        config = ClientConfig(headers={"existing": "value"})
        new_config = config.with_headers()
        
        assert new_config.headers == {"existing": "value"}
    
    def test_with_auth_empty_string(self):
        config = ClientConfig().with_auth("")
        
        assert config.auth_token == ""
    
    def test_dataclass_equality(self):
        config1 = ClientConfig(user_id="alice", user_name="Alice")
        config2 = ClientConfig(user_id="alice", user_name="Alice")
        
        assert config1 == config2
    
    def test_dataclass_inequality(self):
        config1 = ClientConfig(user_id="alice")
        config2 = ClientConfig(user_id="bob")
        
        assert config1 != config2
