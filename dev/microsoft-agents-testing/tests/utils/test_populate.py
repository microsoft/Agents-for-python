# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from microsoft_agents.activity import Activity, ChannelAccount, ConversationAccount

from microsoft_agents.testing.utils.populate import (
    update_with_defaults,
    populate_activity,
)


class TestUpdateWithDefaults:
    """Tests for the update_with_defaults function."""

    def test_update_with_defaults_with_empty_original(self):
        """Test that defaults are added to an empty dictionary."""
        original = {}
        defaults = {"key1": "value1", "key2": "value2"}
        update_with_defaults(original, defaults)
        assert original == {"key1": "value1", "key2": "value2"}

    def test_update_with_defaults_with_empty_defaults(self):
        """Test that original dictionary is unchanged when defaults is empty."""
        original = {"key1": "value1"}
        defaults = {}
        update_with_defaults(original, defaults)
        assert original == {"key1": "value1"}

    def test_update_with_defaults_with_non_overlapping_keys(self):
        """Test that defaults are added when keys don't overlap."""
        original = {"key1": "value1"}
        defaults = {"key2": "value2", "key3": "value3"}
        update_with_defaults(original, defaults)
        assert original == {"key1": "value1", "key2": "value2", "key3": "value3"}

    def test_update_with_defaults_preserves_existing_values(self):
        """Test that existing values in original are not overwritten."""
        original = {"key1": "original_value", "key2": "value2"}
        defaults = {"key1": "default_value", "key3": "value3"}
        update_with_defaults(original, defaults)
        assert original == {
            "key1": "original_value",
            "key2": "value2",
            "key3": "value3",
        }

    def test_update_with_defaults_with_nested_dicts(self):
        """Test that nested dictionaries are recursively updated."""
        original = {"nested": {"key1": "original"}}
        defaults = {"nested": {"key1": "default", "key2": "value2"}}
        update_with_defaults(original, defaults)
        assert original == {"nested": {"key1": "original", "key2": "value2"}}

    def test_update_with_defaults_with_deeply_nested_dicts(self):
        """Test recursive update with deeply nested structures."""
        original = {"level1": {"level2": {"key1": "original"}}}
        defaults = {
            "level1": {
                "level2": {"key1": "default", "key2": "value2"},
                "level2b": {"key3": "value3"},
            }
        }
        update_with_defaults(original, defaults)
        assert original == {
            "level1": {
                "level2": {"key1": "original", "key2": "value2"},
                "level2b": {"key3": "value3"},
            }
        }

    def test_update_with_defaults_adds_nested_dict_when_missing(self):
        """Test that nested dicts are added when they don't exist in original."""
        original = {"key1": "value1"}
        defaults = {"nested": {"key2": "value2"}}
        update_with_defaults(original, defaults)
        assert original == {"key1": "value1", "nested": {"key2": "value2"}}

    def test_update_with_defaults_with_mixed_types(self):
        """Test with various value types: strings, numbers, booleans, lists."""
        original = {"str": "text", "num": 42}
        defaults = {
            "str": "default_text",
            "bool": True,
            "list": [1, 2, 3],
            "none": None,
        }
        update_with_defaults(original, defaults)
        assert original == {
            "str": "text",
            "num": 42,
            "bool": True,
            "list": [1, 2, 3],
            "none": None,
        }

    def test_update_with_defaults_with_none_values(self):
        """Test that None values in defaults are added."""
        original = {"key1": "value1"}
        defaults = {"key2": None}
        update_with_defaults(original, defaults)
        assert original == {"key1": "value1", "key2": None}

    def test_update_with_defaults_preserves_none_in_original(self):
        """Test that None values in original are preserved."""
        original = {"key1": None}
        defaults = {"key1": "default_value"}
        update_with_defaults(original, defaults)
        assert original == {"key1": None}

    def test_update_with_defaults_with_list_values(self):
        """Test that list values are not merged, only added if missing."""
        original = {"list1": [1, 2]}
        defaults = {"list1": [3, 4], "list2": [5, 6]}
        update_with_defaults(original, defaults)
        assert original == {"list1": [1, 2], "list2": [5, 6]}

    def test_update_with_defaults_type_mismatch_original_wins(self):
        """Test that when types differ, original value is preserved."""
        original = {"key1": "string_value"}
        defaults = {"key1": {"nested": "dict"}}
        update_with_defaults(original, defaults)
        assert original == {"key1": "string_value"}

    def test_update_with_defaults_type_mismatch_defaults_dict(self):
        """Test that when original is dict and default is not, original is preserved."""
        original = {"key1": {"nested": "dict"}}
        defaults = {"key1": "string_value"}
        update_with_defaults(original, defaults)
        assert original == {"key1": {"nested": "dict"}}

    def test_update_with_defaults_modifies_in_place(self):
        """Test that the function modifies the original dict in place."""
        original = {"key1": "value1"}
        original_id = id(original)
        defaults = {"key2": "value2"}
        update_with_defaults(original, defaults)
        assert id(original) == original_id
        assert original == {"key1": "value1", "key2": "value2"}

    def test_update_with_defaults_with_complex_nested_structure(self):
        """Test with complex real-world-like nested structure."""
        original = {
            "user": {"name": "Alice", "settings": {"theme": "dark"}},
            "timestamp": "2025-01-01",
        }
        defaults = {
            "user": {
                "name": "DefaultName",
                "settings": {"theme": "light", "language": "en"},
                "role": "user",
            },
            "channel": "default-channel",
        }
        update_with_defaults(original, defaults)
        assert original == {
            "user": {
                "name": "Alice",
                "settings": {"theme": "dark", "language": "en"},
                "role": "user",
            },
            "timestamp": "2025-01-01",
            "channel": "default-channel",
        }


class TestPopulateActivity:
    """Tests for the populate_activity function."""

    def test_populate_activity_with_none_values_filled(self):
        """Test that None values in original are replaced with defaults."""
        original = Activity(type="message")
        defaults = Activity(type="message", text="Default text")
        result = populate_activity(original, defaults)
        assert result.text == "Default text"
        assert result.type == "message"

    def test_populate_activity_preserves_existing_values(self):
        """Test that existing non-None values are preserved."""
        original = Activity(type="message", text="Original text")
        defaults = Activity(type="event", text="Default text")
        result = populate_activity(original, defaults)
        assert result.text == "Original text"
        assert result.type == "message"

    def test_populate_activity_returns_new_instance(self):
        """Test that a new Activity instance is returned."""
        original = Activity(type="message", text="Original")
        defaults = {"text": "Default text"}
        result = populate_activity(original, defaults)
        assert result is not original
        assert id(result) != id(original)

    def test_populate_activity_original_unchanged(self):
        """Test that the original Activity is not modified."""
        original = Activity(type="message")
        defaults = Activity(type="message", text="Default text")
        original_text = original.text
        result = populate_activity(original, defaults)
        assert original.text == original_text
        assert result.text == "Default text"

    def test_populate_activity_with_dict_defaults(self):
        """Test that defaults can be provided as a dictionary."""
        original = Activity(type="message")
        original.channel_id = "channel"
        defaults = {"text": "Default text", "channel_id": "default-channel"}
        result = populate_activity(original, defaults)
        assert result.text == "Default text"
        assert result.channel_id == "channel"

    def test_populate_activity_with_activity_defaults(self):
        """Test that defaults can be provided as an Activity object."""
        original = Activity(type="message")
        defaults = Activity(type="event", text="Default text", channel_id="channel")
        result = populate_activity(original, defaults)
        assert result.text == "Default text"

    def test_populate_activity_with_empty_defaults(self):
        """Test that original is unchanged when defaults is empty."""
        original = Activity(type="message", text="Original text")
        defaults = {}
        result = populate_activity(original, defaults)
        assert result.text == "Original text"
        assert result.type == "message"

    def test_populate_activity_with_multiple_fields(self):
        """Test populating multiple None fields."""
        original = Activity(
            type="message",
        )
        defaults = {
            "text": "Default text",
            "channel_id": "default-channel",
            "locale": "en-US",
        }
        result = populate_activity(original, defaults)
        assert result.text == "Default text"
        assert result.channel_id == "default-channel"
        assert result.locale == "en-US"

    def test_populate_activity_with_complex_objects(self):
        """Test populating with complex nested objects."""
        original = Activity(type="message")
        defaults = Activity(
            type="invoke",
            from_property=ChannelAccount(id="bot123", name="Bot"),
            conversation=ConversationAccount(id="conv123", name="Conversation"),
        )
        result = populate_activity(original, defaults)
        assert result.from_property is not None
        assert result.from_property.id == "bot123"
        assert result.conversation is not None
        assert result.conversation.id == "conv123"

    def test_populate_activity_preserves_complex_objects(self):
        """Test that existing complex objects are preserved."""
        original = Activity(
            type="message",
            from_property=ChannelAccount(id="user456", name="User"),
        )
        defaults = Activity(
            type="invoke", from_property=ChannelAccount(id="bot123", name="Bot")
        )
        result = populate_activity(original, defaults)
        assert result.from_property.id == "user456"

    def test_populate_activity_partial_defaults(self):
        """Test that only specified defaults are applied."""
        original = Activity(type="message")
        defaults = {"text": "Default text"}
        result = populate_activity(original, defaults)
        assert result.text == "Default text"
        assert result.channel_id is None

    def test_populate_activity_with_zero_and_empty_string(self):
        """Test that zero and empty string are considered as set values."""
        original = Activity(type="message", text="")
        defaults = {"text": "Default text", "locale": "en-US"}
        result = populate_activity(original, defaults)
        # Empty strings should be preserved as they are not None
        assert result.text == ""
        assert result.locale == "en-US"

    def test_populate_activity_with_false_boolean(self):
        """Test that False boolean values are preserved."""
        original = Activity(type="message")
        original.history_disclosed = False
        defaults = {"history_disclosed": True}
        result = populate_activity(original, defaults)
        # False should be preserved as it's not None
        assert result.history_disclosed is False

    def test_populate_activity_with_zero_numeric(self):
        """Test that numeric zero values are preserved."""
        original = Activity(type="message")
        # Assuming there's a numeric field we can test
        original.channel_data = {"count": 0}
        defaults = {"channel_data": {"count": 10}}
        result = populate_activity(original, defaults)
        # Zero should be preserved
        assert result.channel_data == {"count": 0}

    def test_populate_activity_defaults_from_activity_excludes_unset(self):
        """Test that only explicitly set fields from Activity defaults are used."""
        original = Activity(type="message")
        # Create defaults with only type set explicitly
        defaults = Activity(type="event")
        result = populate_activity(original, defaults)
        # Since defaults Activity didn't explicitly set text, it should remain None
        assert result.text is None

    def test_populate_activity_with_empty_activity_defaults(self):
        """Test with an Activity that has no fields set."""
        original = Activity(type="message")
        defaults = {}
        result = populate_activity(original, defaults)
        assert result.type == "message"
        assert result.text is None

    def test_populate_activity_real_world_scenario(self):
        """Test a real-world scenario of populating a bot response."""
        original = Activity(
            type="message",
            text="User's query result",
            from_property=ChannelAccount(id="bot123"),
        )
        defaults = {
            "conversation": ConversationAccount(id="default-conv"),
            "channel_id": "teams",
            "locale": "en-US",
        }
        result = populate_activity(original, defaults)
        assert result.text == "User's query result"
        assert result.from_property.id == "bot123"
        assert result.conversation.id == "default-conv"
        assert result.channel_id == "teams"
        assert result.locale == "en-US"

    def test_populate_activity_with_list_fields(self):
        """Test populating list fields like attachments or entities."""
        original = Activity(type="message")
        defaults = {"attachments": [], "entities": []}
        result = populate_activity(original, defaults)
        assert result.attachments == []
        assert result.entities == []

    def test_populate_activity_preserves_empty_lists(self):
        """Test that empty lists in original are preserved."""
        original = Activity(type="message", attachments=[], entities=[])
        defaults = {
            "attachments": [{"type": "card"}],
            "entities": [{"type": "mention"}],
        }
        result = populate_activity(original, defaults)
        # Empty lists are not None, so they should be preserved
        assert result.attachments == []
        assert result.entities == []
