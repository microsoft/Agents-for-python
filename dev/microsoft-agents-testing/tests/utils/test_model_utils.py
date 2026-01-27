"""
Unit tests for model_utils module.

This module tests:
- normalize_model_data: Normalizing BaseModel and dict data
- ModelTemplate: Template for creating BaseModel instances with defaults
- ActivityTemplate: Specialized template for Activity instances
"""

import pytest
from copy import deepcopy
from pydantic import BaseModel
from typing import Optional

from microsoft_agents.testing.utils.model_utils import (
    normalize_model_data,
    ModelTemplate,
    ActivityTemplate,
)
from microsoft_agents.activity import Activity


# =============================================================================
# Test Fixtures - Simple Pydantic Models for Testing
# =============================================================================

class SimpleModel(BaseModel):
    """A simple model for testing."""
    name: Optional[str] = None
    value: Optional[int] = None


class NestedModel(BaseModel):
    """A model with nested structure for testing."""
    title: Optional[str] = None
    data: Optional[SimpleModel] = None


class ComplexModel(BaseModel):
    """A more complex model for testing."""
    id: Optional[str] = None
    name: Optional[str] = None
    count: Optional[int] = None
    active: Optional[bool] = None
    tags: Optional[list] = None
    metadata: Optional[dict] = None


# =============================================================================
# normalize_model_data() Tests
# =============================================================================

class TestNormalizeModelData:
    """Test normalize_model_data function."""

    def test_normalize_dict_input(self):
        """Test normalizing a plain dictionary."""
        data = {"name": "test", "value": 42}
        result = normalize_model_data(data)
        assert result == {"name": "test", "value": 42}

    def test_normalize_dict_creates_deep_copy(self):
        """Test that normalizing a dict expands it (deep copy behavior)."""
        data = {"a.b": 1}
        result = normalize_model_data(data)
        # expand() is called, so dot notation is expanded
        assert result == {"a": {"b": 1}}

    def test_normalize_basemodel_input(self):
        """Test normalizing a Pydantic BaseModel."""
        model = SimpleModel(name="test", value=42)
        result = normalize_model_data(model)
        assert result == {"name": "test", "value": 42}

    def test_normalize_basemodel_excludes_unset(self):
        """Test that unset fields are excluded from normalized output."""
        model = SimpleModel(name="test")
        result = normalize_model_data(model)
        assert result == {"name": "test"}
        assert "value" not in result

    def test_normalize_nested_model(self):
        """Test normalizing a nested Pydantic model."""
        inner = SimpleModel(name="inner", value=10)
        outer = NestedModel(title="outer", data=inner)
        result = normalize_model_data(outer)
        assert result == {
            "title": "outer",
            "data": {"name": "inner", "value": 10}
        }

    def test_normalize_empty_dict(self):
        """Test normalizing an empty dictionary."""
        result = normalize_model_data({})
        assert result == {}

    def test_normalize_empty_model(self):
        """Test normalizing a model with no fields set."""
        model = SimpleModel()
        result = normalize_model_data(model)
        assert result == {}

    def test_normalize_dict_with_nested_structure(self):
        """Test normalizing a dict with already nested structure."""
        data = {"outer": {"inner": "value"}}
        result = normalize_model_data(data)
        assert result == {"outer": {"inner": "value"}}

    def test_normalize_activity_model(self):
        """Test normalizing an Activity model."""
        activity = Activity(type="message", text="Hello")
        result = normalize_model_data(activity)
        assert result["type"] == "message"
        assert result["text"] == "Hello"


# =============================================================================
# ModelTemplate Tests
# =============================================================================

class TestModelTemplate:
    """Test ModelTemplate class."""

    # -------------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------------

    def test_init_with_no_defaults(self):
        """Test creating a template with no defaults."""
        template = ModelTemplate(SimpleModel)
        assert template._defaults == {}
        assert template._model_class == SimpleModel

    def test_init_with_dict_defaults(self):
        """Test creating a template with dict defaults."""
        defaults = {"name": "default_name", "value": 100}
        template = ModelTemplate(SimpleModel, defaults)
        assert template._defaults == {"name": "default_name", "value": 100}

    def test_init_with_model_defaults(self):
        """Test creating a template with BaseModel defaults."""
        defaults = SimpleModel(name="default_name", value=100)
        template = ModelTemplate(SimpleModel, defaults)
        assert template._defaults == {"name": "default_name", "value": 100}

    def test_init_with_kwargs(self):
        """Test creating a template with keyword arguments."""
        template = ModelTemplate(SimpleModel, name="kwarg_name", value=50)
        assert template._defaults == {"name": "kwarg_name", "value": 50}

    def test_init_with_defaults_and_kwargs(self):
        """Test creating a template with both defaults and kwargs."""
        defaults = {"name": "default_name"}
        template = ModelTemplate(SimpleModel, defaults, value=75)
        assert template._defaults == {"name": "default_name", "value": 75}

    # -------------------------------------------------------------------------
    # create() Tests
    # -------------------------------------------------------------------------

    def test_create_with_no_original(self):
        """Test creating a model with only defaults."""
        template = ModelTemplate(SimpleModel, {"name": "default", "value": 10})
        result = template.create()
        assert isinstance(result, SimpleModel)
        assert result.name == "default"
        assert result.value == 10

    def test_create_with_dict_original(self):
        """Test creating a model with dict original overriding defaults."""
        template = ModelTemplate(SimpleModel, {"name": "default", "value": 10})
        result = template.create({"name": "override"})
        assert result.name == "override"
        assert result.value == 10

    def test_create_with_model_original(self):
        """Test creating a model with BaseModel original overriding defaults."""
        template = ModelTemplate(SimpleModel, {"name": "default", "value": 10})
        original = SimpleModel(name="override")
        result = template.create(original)
        assert result.name == "override"
        assert result.value == 10

    def test_create_with_empty_dict(self):
        """Test creating a model with empty dict uses defaults."""
        template = ModelTemplate(SimpleModel, {"name": "default"})
        result = template.create({})
        assert result.name == "default"

    def test_create_with_none(self):
        """Test creating a model with None uses defaults."""
        template = ModelTemplate(SimpleModel, {"name": "default"})
        result = template.create(None)
        assert result.name == "default"

    def test_create_complex_model(self):
        """Test creating a complex model with various field types."""
        template = ModelTemplate(ComplexModel, {
            "id": "default_id",
            "active": True,
            "tags": ["tag1"]
        })
        result = template.create({"name": "test", "count": 5})
        assert result.id == "default_id"
        assert result.name == "test"
        assert result.count == 5
        assert result.active is True
        assert result.tags == ["tag1"]

    def test_create_preserves_original_not_mutated(self):
        """Test that create doesn't mutate the original dict."""
        template = ModelTemplate(SimpleModel, {"name": "default"})
        original = {"value": 42}
        original_copy = deepcopy(original)
        template.create(original)
        assert original == original_copy

    # -------------------------------------------------------------------------
    # with_defaults() Tests
    # -------------------------------------------------------------------------

    def test_with_defaults_creates_new_template(self):
        """Test that with_defaults creates a new template instance."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_defaults({"value": 100})
        assert template1 is not template2

    def test_with_defaults_preserves_original(self):
        """Test that with_defaults doesn't modify the original template."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template1.with_defaults({"value": 100})
        assert template1._defaults == {"name": "original"}

    def test_with_defaults_merges_defaults(self):
        """Test that with_defaults merges new defaults with existing."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_defaults({"value": 100})
        assert template2._defaults == {"name": "original", "value": 100}

    def test_with_defaults_with_kwargs(self):
        """Test with_defaults using keyword arguments."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_defaults(value=200)
        assert template2._defaults == {"name": "original", "value": 200}

    def test_with_defaults_does_not_override_existing(self):
        """Test that with_defaults sets defaults (doesn't override existing)."""
        template1 = ModelTemplate(SimpleModel, {"name": "original", "value": 50})
        template2 = template1.with_defaults({"name": "new", "value": 100})
        # set_defaults should not override existing values
        assert template2._defaults == {"name": "original", "value": 50}

    def test_with_defaults_nested_structure(self):
        """Test with_defaults with nested structure."""
        template1 = ModelTemplate(NestedModel, {"title": "test"})
        template2 = template1.with_defaults({"data": {"name": "nested"}})
        assert template2._defaults == {
            "title": "test",
            "data": {"name": "nested"}
        }

    # -------------------------------------------------------------------------
    # with_updates() Tests
    # -------------------------------------------------------------------------

    def test_with_updates_creates_new_template(self):
        """Test that with_updates creates a new template instance."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_updates({"name": "updated"})
        assert template1 is not template2

    def test_with_updates_preserves_original(self):
        """Test that with_updates doesn't modify the original template."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template1.with_updates({"name": "updated"})
        assert template1._defaults == {"name": "original"}

    def test_with_updates_overrides_values(self):
        """Test that with_updates overrides existing values."""
        template1 = ModelTemplate(SimpleModel, {"name": "original", "value": 10})
        template2 = template1.with_updates({"name": "updated"})
        assert template2._defaults == {"name": "updated", "value": 10}

    def test_with_updates_with_kwargs(self):
        """Test with_updates using keyword arguments."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_updates(name="updated", value=99)
        assert template2._defaults == {"name": "updated", "value": 99}

    def test_with_updates_with_dot_notation(self):
        """Test with_updates with dot notation for nested updates."""
        template1 = ModelTemplate(NestedModel, {"title": "test", "data": {"name": "old", "value": 1}})
        template2 = template1.with_updates(**{"data.name": "new"})
        assert template2._defaults == {
            "title": "test",
            "data": {"name": "new", "value": 1}
        }

    def test_with_updates_adds_new_fields(self):
        """Test that with_updates can add new fields."""
        template1 = ModelTemplate(SimpleModel, {"name": "original"})
        template2 = template1.with_updates({"value": 42})
        assert template2._defaults == {"name": "original", "value": 42}

    def test_with_updates_deep_merge(self):
        """Test that with_updates performs deep merge on nested dicts."""
        template1 = ModelTemplate(ComplexModel, {
            "id": "123",
            "metadata": {"key1": "val1", "key2": "val2"}
        })
        template2 = template1.with_updates({"metadata": {"key2": "updated"}})
        assert template2._defaults == {
            "id": "123",
            "metadata": {"key1": "val1", "key2": "updated"}
        }

    # -------------------------------------------------------------------------
    # Equality Tests
    # -------------------------------------------------------------------------

    def test_equality_same_templates(self):
        """Test equality between identical templates."""
        template1 = ModelTemplate(SimpleModel, {"name": "test", "value": 42})
        template2 = ModelTemplate(SimpleModel, {"name": "test", "value": 42})
        assert template1 == template2

    def test_equality_different_defaults(self):
        """Test inequality with different defaults."""
        template1 = ModelTemplate(SimpleModel, {"name": "test1"})
        template2 = ModelTemplate(SimpleModel, {"name": "test2"})
        assert template1 != template2

    def test_equality_different_model_class(self):
        """Test inequality with different model classes."""
        template1 = ModelTemplate(SimpleModel, {"name": "test"})
        template2 = ModelTemplate(ComplexModel, {"name": "test"})
        assert template1 != template2

    def test_equality_with_non_template(self):
        """Test inequality with non-ModelTemplate objects."""
        template = ModelTemplate(SimpleModel, {"name": "test"})
        assert template != {"name": "test"}
        assert template != "not a template"
        assert template != None

    def test_equality_empty_templates(self):
        """Test equality between empty templates of same type."""
        template1 = ModelTemplate(SimpleModel)
        template2 = ModelTemplate(SimpleModel)
        assert template1 == template2


# =============================================================================
# ActivityTemplate Tests
# =============================================================================

class TestActivityTemplate:
    """Test ActivityTemplate class."""

    def test_init_with_no_defaults(self):
        """Test creating an ActivityTemplate with no defaults."""
        template = ActivityTemplate()
        assert template._defaults == {}
        assert template._model_class == Activity

    def test_init_with_dict_defaults(self):
        """Test creating an ActivityTemplate with dict defaults."""
        defaults = {"type": "message", "text": "Hello"}
        template = ActivityTemplate(defaults)
        assert template._defaults == {"type": "message", "text": "Hello"}

    def test_init_with_activity_defaults(self):
        """Test creating an ActivityTemplate with Activity defaults."""
        defaults = Activity(type="message", text="Hello")
        template = ActivityTemplate(defaults)
        assert template._defaults["type"] == "message"
        assert template._defaults["text"] == "Hello"

    def test_init_with_kwargs(self):
        """Test creating an ActivityTemplate with keyword arguments."""
        template = ActivityTemplate(type="event", name="test_event")
        assert template._defaults["type"] == "event"
        assert template._defaults["name"] == "test_event"

    def test_create_activity(self):
        """Test creating an Activity from template."""
        template = ActivityTemplate({"type": "message", "text": "default"})
        result = template.create()
        assert isinstance(result, Activity)
        assert result.type == "message"
        assert result.text == "default"

    def test_create_activity_with_override(self):
        """Test creating an Activity with overridden values."""
        template = ActivityTemplate({"type": "message", "text": "default"})
        result = template.create({"text": "custom"})
        assert result.type == "message"
        assert result.text == "custom"

    def test_create_activity_with_activity_original(self):
        """Test creating an Activity from another Activity."""
        template = ActivityTemplate({"type": "message", "text": "default"})
        original = {"text": "from_activity"}
        result = template.create(original)
        assert result.type == "message"
        assert result.text == "from_activity"

    def test_with_defaults_returns_model_template(self):
        """Test that with_defaults returns a ModelTemplate."""
        template = ActivityTemplate({"type": "message"})
        new_template = template.with_defaults({"text": "added"})
        assert isinstance(new_template, ModelTemplate)
        assert new_template._model_class == Activity

    def test_with_updates_returns_model_template(self):
        """Test that with_updates returns a ModelTemplate."""
        template = ActivityTemplate({"type": "message"})
        new_template = template.with_updates({"type": "event"})
        assert isinstance(new_template, ModelTemplate)
        assert new_template._defaults["type"] == "event"

    def test_activity_with_nested_from_field(self):
        """Test Activity template with nested from field."""
        template = ActivityTemplate({
            "type": "message",
            "from_property": {"id": "bot_id", "name": "Bot"}
        })
        result = template.create()
        assert result.type == "message"
        # Note: Activity uses from_property for the 'from' field
        assert result.from_property.id == "bot_id"
        assert result.from_property.name == "Bot"

    def test_activity_with_conversation(self):
        """Test Activity template with conversation reference."""
        template = ActivityTemplate({
            "type": "message",
            "conversation": {"id": "conv_123"}
        })
        result = template.create()
        assert result.conversation.id == "conv_123"

    def test_inheritance_from_model_template(self):
        """Test that ActivityTemplate inherits from ModelTemplate."""
        template = ActivityTemplate()
        assert isinstance(template, ModelTemplate)


# =============================================================================
# Integration Tests
# =============================================================================

class TestModelTemplateIntegration:
    """Integration tests for ModelTemplate workflows."""

    def test_chained_with_defaults(self):
        """Test chaining multiple with_defaults calls."""
        template = ModelTemplate(ComplexModel)
        template = template.with_defaults({"id": "base_id"})
        template = template.with_defaults({"name": "base_name"})
        template = template.with_defaults({"count": 0})
        
        result = template.create()
        assert result.id == "base_id"
        assert result.name == "base_name"
        assert result.count == 0

    def test_chained_with_updates(self):
        """Test chaining multiple with_updates calls."""
        template = ModelTemplate(SimpleModel, {"name": "original", "value": 1})
        template = template.with_updates({"value": 2})
        template = template.with_updates({"value": 3})
        
        result = template.create()
        assert result.name == "original"
        assert result.value == 3

    def test_mixed_with_defaults_and_updates(self):
        """Test mixing with_defaults and with_updates."""
        template = ModelTemplate(SimpleModel, {"name": "base"})
        template = template.with_defaults({"value": 10})
        template = template.with_updates({"name": "updated"})
        
        result = template.create()
        assert result.name == "updated"
        assert result.value == 10

    def test_create_multiple_instances(self):
        """Test creating multiple independent instances from same template."""
        template = ModelTemplate(SimpleModel, {"name": "shared", "value": 0})
        
        result1 = template.create({"value": 1})
        result2 = template.create({"value": 2})
        
        assert result1.value == 1
        assert result2.value == 2
        assert result1.name == result2.name == "shared"

    def test_activity_workflow(self):
        """Test typical Activity template workflow."""
        # Create base template for messages
        message_template = ActivityTemplate({
            "type": "message",
            "channel_id": "test-channel",
            "conversation": {"id": "conv-123"}
        })
        
        # Create user message
        user_msg = message_template.create({
            "text": "Hello bot!",
            "from_property": {"id": "user-1", "name": "User"}
        })
        assert user_msg.type == "message"
        assert user_msg.text == "Hello bot!"
        assert user_msg.channel_id == "test-channel"
        
        # Create bot response using same template
        bot_msg = message_template.create({
            "text": "Hello user!",
            "from_property": {"id": "bot-1", "name": "Bot"}
        })
        assert bot_msg.type == "message"
        assert bot_msg.text == "Hello user!"
        assert bot_msg.conversation.id == "conv-123"