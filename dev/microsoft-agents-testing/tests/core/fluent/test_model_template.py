# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ModelTemplate class."""

import pytest
from pydantic import BaseModel

from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, ConversationAccount
from microsoft_agents.testing.core.fluent.model_template import ModelTemplate, ActivityTemplate


class SimpleModel(BaseModel):
    """A simple Pydantic model for testing."""

    name: str
    value: int = 0


class NestedModel(BaseModel):
    """A Pydantic model with nested structure."""

    title: str
    metadata: dict = {}


class ComplexModel(BaseModel):
    """A more complex Pydantic model for testing."""

    name: str
    value: int = 0
    active: bool = True
    tags: list[str] = []


class TestModelTemplateInit:
    """Tests for ModelTemplate initialization."""

    def test_init_with_no_defaults(self):
        """ModelTemplate initializes with no defaults."""
        template = ModelTemplate(SimpleModel)
        assert template._model_class == SimpleModel
        assert template._defaults == {}

    def test_init_with_dict_defaults(self):
        """ModelTemplate initializes with dictionary defaults."""
        defaults = {"name": "default", "value": 42}
        template = ModelTemplate(SimpleModel, defaults)
        assert template._defaults == defaults

    def test_init_with_kwargs_defaults(self):
        """ModelTemplate initializes with keyword argument defaults."""
        template = ModelTemplate(SimpleModel, name="default", value=10)
        assert template._defaults["name"] == "default"
        assert template._defaults["value"] == 10

    def test_init_with_both_dict_and_kwargs(self):
        """ModelTemplate merges dict and kwargs defaults."""
        defaults = {"name": "default"}
        template = ModelTemplate(SimpleModel, defaults, value=100)
        assert template._defaults["name"] == "default"
        assert template._defaults["value"] == 100

    def test_init_with_pydantic_model_defaults(self):
        """ModelTemplate initializes with Pydantic model as defaults."""
        default_model = SimpleModel(name="default", value=5)
        template = ModelTemplate(SimpleModel, default_model)
        assert template._defaults["name"] == "default"
        assert template._defaults["value"] == 5

    def test_init_with_nested_dot_notation(self):
        """ModelTemplate expands dot notation in defaults."""
        template = ModelTemplate(NestedModel, title="Test", **{"metadata.key": "value"})
        assert "metadata.key" in template._defaults
        assert template._defaults["metadata.key"] == "value"


class TestModelTemplateCreate:
    """Tests for the create() method."""

    def test_create_with_no_original(self):
        """create() produces model with only defaults."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        model = template.create()
        assert model.name == "default"
        assert model.value == 42

    def test_create_with_empty_dict(self):
        """create() with empty dict uses defaults."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        model = template.create({})
        assert model.name == "default"
        assert model.value == 42

    def test_create_with_dict_overrides_defaults(self):
        """create() with dict overrides defaults."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        model = template.create({"name": "custom"})
        assert model.name == "custom"
        assert model.value == 42

    def test_create_with_pydantic_model(self):
        """create() works with Pydantic model as original."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        original = SimpleModel(name="original", value=100)
        model = template.create(original)
        assert model.name == "original"
        assert model.value == 100

    def test_create_preserves_non_overridden_defaults(self):
        """create() preserves defaults not overridden by original."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        model = template.create({"name": "custom"})
        assert model.name == "custom"
        assert model.value == 42  # Default preserved

    def test_create_returns_correct_type(self):
        """create() returns an instance of the model class."""
        template = ModelTemplate(SimpleModel, name="test", value=1)
        model = template.create()
        assert isinstance(model, SimpleModel)

    def test_create_with_nested_dict(self):
        """create() handles nested dictionaries."""
        template = ModelTemplate(NestedModel, title="Default")
        model = template.create({"title": "Custom", "metadata": {"key": "value"}})
        assert model.title == "Custom"
        assert model.metadata == {"key": "value"}

    def test_create_with_nested_defaults(self):
        """create() merges nested defaults correctly."""
        template = ModelTemplate(NestedModel, title="Default", **{"metadata.key1": "v1"})
        model = template.create({"metadata": {"key2": "v2"}})
        # Original overwrites defaults since it's a complete dictionary
        assert model.title == "Default"
        assert model.metadata.get("key2") == "v2"


class TestModelTemplateEquality:
    """Tests for the __eq__() method."""

    def test_equality_with_same_defaults(self):
        """Two templates with same class and defaults are equal."""
        template1 = ModelTemplate(SimpleModel, name="default", value=42)
        template2 = ModelTemplate(SimpleModel, name="default", value=42)
        assert template1 == template2

    def test_inequality_with_different_defaults(self):
        """Two templates with different defaults are not equal."""
        template1 = ModelTemplate(SimpleModel, name="default", value=42)
        template2 = ModelTemplate(SimpleModel, name="other", value=42)
        assert template1 != template2

    def test_inequality_with_different_model_class(self):
        """Two templates with different model classes are not equal."""
        template1 = ModelTemplate(SimpleModel, name="default", value=42)
        template2 = ModelTemplate(ComplexModel, name="default", value=42)
        assert template1 != template2

    def test_inequality_with_non_template(self):
        """ModelTemplate is not equal to non-template objects."""
        template = ModelTemplate(SimpleModel, name="default")
        assert template != {"name": "default"}
        assert template != "not a template"
        assert template != None


class TestModelTemplateWithComplexModel:
    """Tests for ModelTemplate with complex model structures."""

    def test_create_with_list_field(self):
        """create() handles list fields correctly."""
        template = ModelTemplate(ComplexModel, name="test", tags=["default"])
        model = template.create()
        assert model.tags == ["default"]

    def test_create_overrides_list_field(self):
        """create() overrides list field from original."""
        template = ModelTemplate(ComplexModel, name="test", tags=["default"])
        model = template.create({"tags": ["custom1", "custom2"]})
        assert model.tags == ["custom1", "custom2"]

    def test_create_with_all_fields(self):
        """create() handles all complex model fields."""
        template = ModelTemplate(
            ComplexModel,
            name="default",
            value=0,
            active=True,
            tags=["tag1"],
        )
        model = template.create({"name": "custom", "value": 100})
        assert model.name == "custom"
        assert model.value == 100
        assert model.active is True
        assert model.tags == ["tag1"]


class TestModelTemplateMultipleCreates:
    """Tests for creating multiple models from one template."""

    def test_create_multiple_independent_models(self):
        """create() produces independent model instances."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        model1 = template.create({"name": "one"})
        model2 = template.create({"name": "two"})
        
        assert model1.name == "one"
        assert model2.name == "two"
        assert model1 is not model2

    def test_template_unchanged_after_create(self):
        """Template defaults are unchanged after create()."""
        template = ModelTemplate(SimpleModel, name="default", value=42)
        template.create({"name": "custom"})
        
        # Create another to verify defaults
        model = template.create()
        assert model.name == "default"
        assert model.value == 42

class TestActivityTemplateInit:
    """Tests for ActivityTemplate initialization."""

    def test_init_with_no_defaults(self):
        """ActivityTemplate initializes with no defaults."""
        template = ActivityTemplate()
        assert template._model_class == Activity
        assert template._defaults == {}

    def test_init_with_dict_defaults(self):
        """ActivityTemplate initializes with dictionary defaults."""
        defaults = {"type": ActivityTypes.message, "text": "Hello"}
        template = ActivityTemplate(defaults)
        assert template._defaults["type"] == ActivityTypes.message
        assert template._defaults["text"] == "Hello"

    def test_init_with_kwargs_defaults(self):
        """ActivityTemplate initializes with keyword argument defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Hello")
        assert template._defaults["type"] == ActivityTypes.message
        assert template._defaults["text"] == "Hello"

    def test_init_with_both_dict_and_kwargs(self):
        """ActivityTemplate merges dict and kwargs defaults."""
        defaults = {"type": ActivityTypes.message}
        template = ActivityTemplate(defaults, text="Hello")
        assert template._defaults["type"] == ActivityTypes.message
        assert template._defaults["text"] == "Hello"

    def test_init_with_activity_model_defaults(self):
        """ActivityTemplate initializes with Activity model as defaults."""
        default_activity = Activity(type=ActivityTypes.message, text="Default text")
        template = ActivityTemplate(default_activity)
        assert template._defaults["type"] == ActivityTypes.message
        assert template._defaults["text"] == "Default text"


class TestActivityTemplateCreate:
    """Tests for the create() method."""

    def test_create_with_no_original(self):
        """create() produces Activity with only defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        activity = template.create()
        assert isinstance(activity, Activity)
        assert activity.type == ActivityTypes.message
        assert activity.text == "Default"

    def test_create_with_empty_dict(self):
        """create() with empty dict uses defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        activity = template.create({})
        assert activity.type == ActivityTypes.message
        assert activity.text == "Default"

    def test_create_with_dict_overrides_defaults(self):
        """create() with dict overrides defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        activity = template.create({"text": "Custom"})
        assert activity.type == ActivityTypes.message
        assert activity.text == "Custom"

    def test_create_with_activity_overrides_defaults(self):
        """create() with Activity overrides defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        original = Activity(type=ActivityTypes.typing, text="Custom")
        activity = template.create(original)
        assert activity.type == ActivityTypes.typing
        assert activity.text == "Custom"

    def test_create_preserves_none_in_original(self):
        """create() preserves None values from original when overriding defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        # Pass original with no text set (None by default)
        activity = template.create({"type": ActivityTypes.event})
        # Should use the default text when not overridden
        assert activity.type == ActivityTypes.event
        assert activity.text == "Default"


class TestActivityTemplateWithActivityTypes:
    """Tests for ActivityTemplate with various ActivityTypes."""

    def test_create_message_activity(self):
        """ActivityTemplate creates message activities correctly."""
        template = ActivityTemplate(type=ActivityTypes.message)
        activity = template.create({"text": "Hello, World!"})
        assert activity.type == ActivityTypes.message
        assert activity.text == "Hello, World!"

    def test_create_typing_activity(self):
        """ActivityTemplate creates typing activities correctly."""
        template = ActivityTemplate(type=ActivityTypes.typing)
        activity = template.create()
        assert activity.type == ActivityTypes.typing

    def test_create_event_activity(self):
        """ActivityTemplate creates event activities correctly."""
        template = ActivityTemplate(type=ActivityTypes.event, name="testEvent")
        activity = template.create({"value": {"key": "value"}})
        assert activity.type == ActivityTypes.event
        assert activity.name == "testEvent"
        assert activity.value == {"key": "value"}

    def test_create_conversation_update_activity(self):
        """ActivityTemplate creates conversation update activities correctly."""
        template = ActivityTemplate(type=ActivityTypes.conversation_update)
        activity = template.create()
        assert activity.type == ActivityTypes.conversation_update

    def test_create_end_of_conversation_activity(self):
        """ActivityTemplate creates end of conversation activities correctly."""
        template = ActivityTemplate(type=ActivityTypes.end_of_conversation)
        activity = template.create()
        assert activity.type == ActivityTypes.end_of_conversation


class TestActivityTemplateWithNestedModels:
    """Tests for ActivityTemplate with nested Pydantic models."""

    def test_create_with_from_property(self):
        """ActivityTemplate handles from_property correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            from_property={"id": "user123", "name": "Test User"}
        )
        activity = template.create()
        assert activity.from_property is not None
        assert activity.from_property.id == "user123"
        assert activity.from_property.name == "Test User"

    def test_create_with_conversation(self):
        """ActivityTemplate handles conversation property correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            conversation={"id": "conv123", "name": "Test Conversation"}
        )
        activity = template.create()
        assert activity.conversation is not None
        assert activity.conversation.id == "conv123"
        assert activity.conversation.name == "Test Conversation"

    def test_create_with_recipient(self):
        """ActivityTemplate handles recipient property correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            recipient={"id": "bot123", "name": "Test Bot"}
        )
        activity = template.create()
        assert activity.recipient is not None
        assert activity.recipient.id == "bot123"
        assert activity.recipient.name == "Test Bot"

    def test_create_with_channel_account_model(self):
        """ActivityTemplate handles ChannelAccount model correctly."""
        channel_account = ChannelAccount(id="user123", name="Test User")
        template = ActivityTemplate(
            type=ActivityTypes.message,
            from_property=channel_account
        )
        activity = template.create()
        assert activity.from_property.id == "user123"
        assert activity.from_property.name == "Test User"

    def test_create_with_conversation_account_model(self):
        """ActivityTemplate handles ConversationAccount model correctly."""
        conversation = ConversationAccount(id="conv123", name="Test Conversation")
        template = ActivityTemplate(
            type=ActivityTypes.message,
            conversation=conversation
        )
        activity = template.create()
        assert activity.conversation.id == "conv123"
        assert activity.conversation.name == "Test Conversation"


class TestActivityTemplateWithDotNotation:
    """Tests for ActivityTemplate with dot notation in defaults."""

    def test_dot_notation_for_from_property(self):
        """ActivityTemplate expands dot notation for from_property."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            **{"from_property.id": "user123", "from_property.name": "Test User"}
        )
        activity = template.create()
        assert activity.from_property is not None
        assert activity.from_property.id == "user123"
        assert activity.from_property.name == "Test User"

    def test_dot_notation_for_conversation(self):
        """ActivityTemplate expands dot notation for conversation."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            **{"conversation.id": "conv123", "conversation.name": "Test Conv"}
        )
        activity = template.create()
        assert activity.conversation is not None
        assert activity.conversation.id == "conv123"
        assert activity.conversation.name == "Test Conv"


class TestActivityTemplateEquality:
    """Tests for ActivityTemplate equality comparison."""

    def test_equal_templates_with_same_defaults(self):
        """ActivityTemplates with same defaults are equal."""
        template1 = ActivityTemplate(type=ActivityTypes.message, text="Hello")
        template2 = ActivityTemplate(type=ActivityTypes.message, text="Hello")
        assert template1 == template2

    def test_unequal_templates_with_different_defaults(self):
        """ActivityTemplates with different defaults are not equal."""
        template1 = ActivityTemplate(type=ActivityTypes.message, text="Hello")
        template2 = ActivityTemplate(type=ActivityTypes.message, text="Goodbye")
        assert template1 != template2

    def test_unequal_templates_with_different_types(self):
        """ActivityTemplates with different types are not equal."""
        template1 = ActivityTemplate(type=ActivityTypes.message)
        template2 = ActivityTemplate(type=ActivityTypes.typing)
        assert template1 != template2

    def test_template_not_equal_to_non_template(self):
        """ActivityTemplate is not equal to non-ModelTemplate objects."""
        template = ActivityTemplate(type=ActivityTypes.message)
        assert template != {"type": ActivityTypes.message}
        assert template != "not a template"
        assert template != None


class TestActivityTemplateWithComplexData:
    """Tests for ActivityTemplate with complex activity data."""

    def test_create_activity_with_attachments(self):
        """ActivityTemplate creates activities with attachments correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            attachments=[{
                "content_type": "application/vnd.microsoft.card.hero",
                "content": {"title": "Hero Card", "text": "Some text"}
            }]
        )
        activity = template.create()
        assert activity.attachments is not None
        assert len(activity.attachments) == 1
        assert activity.attachments[0].content_type == "application/vnd.microsoft.card.hero"

    def test_create_activity_with_channel_data(self):
        """ActivityTemplate creates activities with channel_data correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            channel_data={"custom_key": "custom_value"}
        )
        activity = template.create()
        assert activity.channel_data is not None
        assert activity.channel_data["custom_key"] == "custom_value"

    def test_create_activity_with_value(self):
        """ActivityTemplate creates activities with value correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.invoke,
            name="invoke/action",
            value={"action": "test", "data": [1, 2, 3]}
        )
        activity = template.create()
        assert activity.value is not None
        assert activity.value["action"] == "test"
        assert activity.value["data"] == [1, 2, 3]

    def test_create_activity_with_service_url(self):
        """ActivityTemplate creates activities with service_url correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            service_url="https://test.botframework.com"
        )
        activity = template.create()
        assert activity.service_url == "https://test.botframework.com"

    def test_create_activity_with_channel_id(self):
        """ActivityTemplate creates activities with channel_id correctly."""
        template = ActivityTemplate(
            type=ActivityTypes.message,
            channel_id="emulator"
        )
        activity = template.create()
        assert activity.channel_id == "emulator"


class TestActivityTemplateImmutability:
    """Tests for ActivityTemplate immutability behavior."""

    def test_create_returns_new_instance(self):
        """create() returns a new Activity instance each time."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Hello")
        activity1 = template.create()
        activity2 = template.create()
        assert activity1 is not activity2
        assert activity1.text == activity2.text

    def test_modifying_created_activity_does_not_affect_template(self):
        """Modifying a created Activity does not affect the template defaults."""
        template = ActivityTemplate(type=ActivityTypes.message, text="Original")
        activity = template.create()
        activity.text = "Modified"
        
        new_activity = template.create()
        assert new_activity.text == "Original"
