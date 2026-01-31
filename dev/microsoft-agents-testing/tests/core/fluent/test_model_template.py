# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the ModelTemplate class."""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.model_template import ModelTemplate


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
        assert "metadata" in template._defaults
        assert template._defaults["metadata"]["key"] == "value"


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
