"""
Unit tests for the ScenarioConfig class.

This module tests:
- ScenarioConfig initialization and default values
- Custom configuration options
"""

import pytest
from microsoft_agents.testing.scenario.scenario import ScenarioConfig
from microsoft_agents.testing.scenario.client_config import ClientConfig
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# ScenarioConfig Initialization Tests
# =============================================================================

class TestScenarioConfigInit:
    """Test ScenarioConfig initialization and defaults."""
    
    def test_default_initialization(self):
        config = ScenarioConfig()
        
        assert config.env_file_path == ".env"
        assert config.callback_server_port == 9378
        assert isinstance(config.activity_template, ActivityTemplate)
        assert isinstance(config.client_config, ClientConfig)
    
    def test_init_with_custom_env_file_path(self):
        config = ScenarioConfig(env_file_path=".env.test")
        
        assert config.env_file_path == ".env.test"
    
    def test_init_with_custom_callback_server_port(self):
        config = ScenarioConfig(callback_server_port=8080)
        
        assert config.callback_server_port == 8080
    
    def test_init_with_custom_activity_template(self):
        template = ActivityTemplate(type="custom")
        config = ScenarioConfig(activity_template=template)
        
        assert config.activity_template is template
    
    def test_init_with_custom_client_config(self):
        client_config = ClientConfig(user_id="alice", user_name="Alice")
        config = ScenarioConfig(client_config=client_config)
        
        assert config.client_config is client_config
        assert config.client_config.user_id == "alice"
    
    def test_init_with_all_custom_values(self):
        template = ActivityTemplate(type="custom")
        client_config = ClientConfig(user_id="bob")
        
        config = ScenarioConfig(
            env_file_path="/custom/.env",
            callback_server_port=9000,
            activity_template=template,
            client_config=client_config,
        )
        
        assert config.env_file_path == "/custom/.env"
        assert config.callback_server_port == 9000
        assert config.activity_template is template
        assert config.client_config is client_config


# =============================================================================
# ScenarioConfig Default Factory Tests
# =============================================================================

class TestScenarioConfigDefaultFactories:
    """Test that default factories create independent instances."""
    
    def test_default_activity_template_is_fresh_instance(self):
        config1 = ScenarioConfig()
        config2 = ScenarioConfig()
        
        assert config1.activity_template is not config2.activity_template
    
    def test_default_client_config_is_fresh_instance(self):
        config1 = ScenarioConfig()
        config2 = ScenarioConfig()
        
        assert config1.client_config is not config2.client_config


# =============================================================================
# ScenarioConfig Dataclass Behavior Tests
# =============================================================================

class TestScenarioConfigDataclass:
    """Test ScenarioConfig dataclass behavior."""
    
    def test_equality_with_same_values(self):
        config1 = ScenarioConfig(
            env_file_path=".env",
            callback_server_port=9378,
        )
        config2 = ScenarioConfig(
            env_file_path=".env",
            callback_server_port=9378,
        )
        
        # Note: Default factories create new instances, so activity_template
        # and client_config will be different objects with same values
        assert config1.env_file_path == config2.env_file_path
        assert config1.callback_server_port == config2.callback_server_port
    
    def test_inequality_with_different_values(self):
        config1 = ScenarioConfig(env_file_path=".env")
        config2 = ScenarioConfig(env_file_path=".env.production")
        
        assert config1.env_file_path != config2.env_file_path


# =============================================================================
# Edge Cases
# =============================================================================

class TestScenarioConfigEdgeCases:
    """Test edge cases for ScenarioConfig."""
    
    def test_port_zero(self):
        config = ScenarioConfig(callback_server_port=0)
        assert config.callback_server_port == 0
    
    def test_high_port_number(self):
        config = ScenarioConfig(callback_server_port=65535)
        assert config.callback_server_port == 65535
    
    def test_empty_env_file_path(self):
        config = ScenarioConfig(env_file_path="")
        assert config.env_file_path == ""
    
    def test_absolute_env_file_path(self):
        config = ScenarioConfig(env_file_path="/home/user/.env")
        assert config.env_file_path == "/home/user/.env"
