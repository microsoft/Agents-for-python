# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Scenario configuration classes."""

import pytest

from microsoft_agents.testing.core.scenario import ScenarioConfig, _default_activity_template
from microsoft_agents.testing.core.client_config import ClientConfig
from microsoft_agents.testing.core.fluent import ActivityTemplate


class TestDefaultActivityTemplate:
    """Tests for the default activity template factory."""

    def test_creates_activity_template(self):
        """_default_activity_template creates an ActivityTemplate."""
        template = _default_activity_template()
        assert isinstance(template, ActivityTemplate)

    def test_has_message_type(self):
        """Default template has message type."""
        template = _default_activity_template()
        assert template._defaults.get("type") == "message"

    def test_has_channel_id(self):
        """Default template has channel_id."""
        template = _default_activity_template()
        assert template._defaults.get("channel_id") == "test"

    def test_has_conversation_id(self):
        """Default template has conversation.id via dot notation."""
        template = _default_activity_template()
        # After expansion, conversation should be a dict
        assert "conversation" in template._defaults
        assert template._defaults["conversation"]["id"] == "test-conversation"

    def test_has_locale(self):
        """Default template has locale."""
        template = _default_activity_template()
        assert template._defaults.get("locale") == "en-US"

    def test_has_from_user(self):
        """Default template has from.id and from.name."""
        template = _default_activity_template()
        assert "from" in template._defaults
        assert template._defaults["from"]["id"] == "user-id"
        assert template._defaults["from"]["name"] == "User"

    def test_has_recipient(self):
        """Default template has recipient.id and recipient.name."""
        template = _default_activity_template()
        assert "recipient" in template._defaults
        assert template._defaults["recipient"]["id"] == "agent-id"
        assert template._defaults["recipient"]["name"] == "Agent"


class TestScenarioConfigInitialization:
    """Tests for ScenarioConfig initialization."""

    def test_default_initialization(self):
        """ScenarioConfig initializes with default values."""
        config = ScenarioConfig()
        
        assert config.env_file_path == ".env"
        assert config.callback_server_port == 9378
        assert isinstance(config.activity_template, ActivityTemplate)
        assert isinstance(config.client_config, ClientConfig)

    def test_custom_env_file_path(self):
        """ScenarioConfig accepts custom env_file_path."""
        config = ScenarioConfig(env_file_path=".env.test")
        
        assert config.env_file_path == ".env.test"

    def test_custom_callback_server_port(self):
        """ScenarioConfig accepts custom callback_server_port."""
        config = ScenarioConfig(callback_server_port=8080)
        
        assert config.callback_server_port == 8080

    def test_custom_activity_template(self):
        """ScenarioConfig accepts custom activity_template."""
        custom_template = ActivityTemplate(channel_id="custom-channel")
        config = ScenarioConfig(activity_template=custom_template)
        
        assert config.activity_template is custom_template

    def test_custom_client_config(self):
        """ScenarioConfig accepts custom client_config."""
        custom_config = ClientConfig(user_id="custom-user")
        config = ScenarioConfig(client_config=custom_config)
        
        assert config.client_config is custom_config


class TestScenarioConfigWithDefaults:
    """Tests for ScenarioConfig with various default combinations."""

    def test_partial_custom_values(self):
        """ScenarioConfig with partial custom values uses defaults for rest."""
        config = ScenarioConfig(
            env_file_path=".env.custom",
            callback_server_port=3000,
        )
        
        assert config.env_file_path == ".env.custom"
        assert config.callback_server_port == 3000
        # Rest should be defaults
        assert isinstance(config.activity_template, ActivityTemplate)
        assert isinstance(config.client_config, ClientConfig)

    def test_all_custom_values(self):
        """ScenarioConfig with all custom values."""
        template = ActivityTemplate(type="event")
        client_config = ClientConfig(user_id="test-user", user_name="Test")
        
        config = ScenarioConfig(
            env_file_path="/path/to/.env",
            callback_server_port=5000,
            activity_template=template,
            client_config=client_config,
        )
        
        assert config.env_file_path == "/path/to/.env"
        assert config.callback_server_port == 5000
        assert config.activity_template is template
        assert config.client_config is client_config


class TestScenarioConfigImmutability:
    """Tests for ScenarioConfig behavior."""

    def test_each_default_is_fresh_instance(self):
        """Each ScenarioConfig gets fresh default instances."""
        config1 = ScenarioConfig()
        config2 = ScenarioConfig()
        
        # Templates should be equal but not the same instance
        assert config1.activity_template == config2.activity_template
        assert config1.activity_template is not config2.activity_template
        
        # Client configs should be equal but not the same instance
        # (dataclass default behavior)
        assert config1.client_config == config2.client_config


class TestScenarioConfigIntegrationWithTemplate:
    """Integration tests for ScenarioConfig with ActivityTemplate."""

    def test_default_template_creates_valid_activities(self):
        """Default template from ScenarioConfig creates valid activities."""
        from microsoft_agents.activity import Activity
        
        config = ScenarioConfig()
        activity = config.activity_template.create({"text": "Hello"})
        
        assert isinstance(activity, Activity)
        assert activity.type == "message"
        assert activity.text == "Hello"
        assert activity.channel_id == "test"

    def test_custom_template_in_config_creates_activities(self):
        """Custom template in ScenarioConfig creates activities correctly."""
        from microsoft_agents.activity import Activity, ActivityTypes
        
        custom_template = ActivityTemplate(
            type=ActivityTypes.event,
            name="custom-event",
            channel_id="custom-channel",
        )
        config = ScenarioConfig(activity_template=custom_template)
        
        activity = config.activity_template.create({"value": {"key": "value"}})
        
        assert activity.type == ActivityTypes.event
        assert activity.name == "custom-event"
        assert activity.channel_id == "custom-channel"
        assert activity.value == {"key": "value"}
