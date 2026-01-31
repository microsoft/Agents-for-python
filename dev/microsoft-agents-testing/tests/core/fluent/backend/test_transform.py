# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the transform module."""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.backend.transform import (
    DictionaryTransform,
    ModelTransform,
)
from microsoft_agents.testing.core.fluent.backend.types import Unset


class TestDictionaryTransformInit:
    """Tests for DictionaryTransform initialization."""

    def test_init_with_none(self):
        """Initializing with None creates an empty root."""
        transform = DictionaryTransform(None)
        assert transform._map == {}

    def test_init_with_empty_dict(self):
        """Initializing with empty dict creates an empty root."""
        transform = DictionaryTransform({})
        assert transform._map == {}

    def test_init_with_dict_values(self):
        """Initializing with dict values creates equality predicates."""
        transform = DictionaryTransform({"a": 1})
        # The value should be converted to a callable
        assert callable(transform._map["a"])

    def test_init_with_kwargs(self):
        """Initializing with kwargs merges them into the root."""
        transform = DictionaryTransform(None, a=1, b=2)
        assert "a" in transform._map
        assert "b" in transform._map

    def test_init_with_dict_and_kwargs(self):
        """Initializing with dict and kwargs merges both."""
        transform = DictionaryTransform({"a": 1}, b=2)
        assert "a" in transform._map
        assert "b" in transform._map

    def test_init_with_nested_dict(self):
        """Initializing with nested dict flattens keys with dots."""
        transform = DictionaryTransform({"a": {"b": 1}})
        # Should be flattened
        assert "a.b" in transform._map
        assert callable(transform._map["a.b"])

    def test_init_with_callable_in_dict(self):
        """Initializing with callable values preserves them."""
        func = lambda x: x > 0
        transform = DictionaryTransform({"check": func})
        # Should preserve the original callable
        assert callable(transform._map["check"])

    def test_init_with_invalid_arg_raises(self):
        """Initializing with invalid arg raises ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary or callable"):
            DictionaryTransform("invalid")

    def test_init_with_invalid_arg_int_raises(self):
        """Initializing with an int raises ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary or callable"):
            DictionaryTransform(123)


class TestDictionaryTransformGet:
    """Tests for DictionaryTransform._get method."""

    def test_get_simple_key(self):
        """_get retrieves a simple key from a dict."""
        actual = {"a": 1, "b": 2}
        result = DictionaryTransform._get(actual, "a")
        assert result == 1

    def test_get_nested_key(self):
        """_get retrieves a nested key using dot notation."""
        actual = {"a": {"b": {"c": 3}}}
        result = DictionaryTransform._get(actual, "a.b.c")
        assert result == 3

    def test_get_missing_key_returns_unset(self):
        """_get returns Unset for a missing key."""
        actual = {"a": 1}
        result = DictionaryTransform._get(actual, "b")
        assert result is Unset

    def test_get_missing_nested_key_returns_unset(self):
        """_get returns Unset for a missing nested key."""
        actual = {"a": {"b": 1}}
        result = DictionaryTransform._get(actual, "a.c")
        assert result is Unset

    def test_get_partial_path_returns_unset(self):
        """_get returns Unset when path traverses non-dict."""
        actual = {"a": 1}
        result = DictionaryTransform._get(actual, "a.b")
        assert result is Unset

    def test_get_empty_dict(self):
        """_get returns Unset for any key in an empty dict."""
        actual = {}
        result = DictionaryTransform._get(actual, "a")
        assert result is Unset


class TestDictionaryTransformInvoke:
    """Tests for DictionaryTransform._invoke method."""

    def test_invoke_with_x_arg(self):
        """_invoke passes value as 'x' argument."""
        transform = DictionaryTransform(None)
        actual = {"a": 5}
        func = lambda x: x * 2
        result = transform._invoke(actual, "a", func)
        assert result == 10

    def test_invoke_with_actual_arg(self):
        """_invoke passes value as 'actual' argument."""
        transform = DictionaryTransform(None)
        actual = {"a": 5}
        func = lambda actual: actual + 1
        result = transform._invoke(actual, "a", func)
        assert result == 6

    def test_invoke_with_missing_key(self):
        """_invoke passes Unset for missing keys."""
        transform = DictionaryTransform(None)
        actual = {"a": 5}
        func = lambda x: x is Unset
        result = transform._invoke(actual, "b", func)
        assert result is True

    def test_invoke_nested_key(self):
        """_invoke works with nested keys."""
        transform = DictionaryTransform(None)
        actual = {"a": {"b": 10}}
        func = lambda x: x > 5
        result = transform._invoke(actual, "a.b", func)
        assert result is True


class TestDictionaryTransformEval:
    """Tests for DictionaryTransform.eval method."""

    def test_eval_simple_predicate(self):
        """eval evaluates a simple predicate."""
        transform = DictionaryTransform({"a": 1})
        actual = {"a": 1}
        result = transform.eval(actual)
        assert result == {"a": True}

    def test_eval_failing_predicate(self):
        """eval returns False for failing predicate."""
        transform = DictionaryTransform({"a": 1})
        actual = {"a": 2}
        result = transform.eval(actual)
        assert result == {"a": False}

    def test_eval_nested_predicate(self):
        """eval evaluates nested predicates and returns expanded result."""
        transform = DictionaryTransform({"a": {"b": 1}})
        actual = {"a": {"b": 1}}
        result = transform.eval(actual)
        assert result == {"a": {"b": True}}

    def test_eval_custom_callable(self):
        """eval works with custom callable predicates."""
        transform = DictionaryTransform({"value": lambda x: x > 0})
        actual = {"value": 5}
        result = transform.eval(actual)
        assert result == {"value": True}

    def test_eval_multiple_predicates(self):
        """eval evaluates multiple predicates."""
        transform = DictionaryTransform({"a": 1, "b": 2})
        actual = {"a": 1, "b": 3}
        result = transform.eval(actual)
        assert result == {"a": True, "b": False}

    def test_eval_deeply_nested(self):
        """eval handles deeply nested predicates."""
        transform = DictionaryTransform({"a": {"b": {"c": 1}}})
        actual = {"a": {"b": {"c": 1}}}
        result = transform.eval(actual)
        assert result == {"a": {"b": {"c": True}}}

    def test_eval_returns_expanded_result(self):
        """eval returns an expanded (nested) result dict."""
        transform = DictionaryTransform({"x": {"y": 10}, "z": 20})
        actual = {"x": {"y": 10}, "z": 20}
        result = transform.eval(actual)
        assert result == {"x": {"y": True}, "z": True}


class TestDictionaryTransformFromArgs:
    """Tests for DictionaryTransform.from_args factory method."""

    def test_from_args_with_dict(self):
        """from_args creates transform from dict."""
        transform = DictionaryTransform.from_args({"a": 1})
        assert isinstance(transform, DictionaryTransform)
        assert "a" in transform._map

    def test_from_args_with_callable(self):
        """from_args creates transform from callable."""
        func = lambda x: x > 0
        transform = DictionaryTransform.from_args(func)
        assert isinstance(transform, DictionaryTransform)

    def test_from_args_with_existing_transform(self):
        """from_args returns existing transform if no kwargs."""
        original = DictionaryTransform({"a": 1})
        result = DictionaryTransform.from_args(original)
        assert result is original

    def test_from_args_with_transform_and_kwargs_raises(self):
        """from_args raises NotImplementedError for transform with kwargs."""
        original = DictionaryTransform({"a": 1})
        with pytest.raises(NotImplementedError, match="not implemented"):
            DictionaryTransform.from_args(original, b=2)

    def test_from_args_with_kwargs(self):
        """from_args creates transform from kwargs."""
        transform = DictionaryTransform.from_args(None, a=1, b=2)
        assert isinstance(transform, DictionaryTransform)
        assert "a" in transform._map
        assert "b" in transform._map


class SampleModel(BaseModel):
    """A sample Pydantic model for testing."""
    name: str
    value: int
    nested: dict | None = None


class TestModelTransform:
    """Tests for the ModelTransform class."""

    def test_init(self):
        """ModelTransform initializes with a DictionaryTransform."""
        dict_transform = DictionaryTransform({"name": "test"})
        model_transform = ModelTransform(dict_transform)
        assert model_transform._dict_transform is dict_transform

    def test_eval_with_dict(self):
        """eval works with a dict source."""
        dict_transform = DictionaryTransform({"name": "test"})
        model_transform = ModelTransform(dict_transform)
        result = model_transform.eval({"name": "test"})
        assert result == [{"name": True}]

    def test_eval_with_pydantic_model(self):
        """eval works with a Pydantic model source."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        model_transform = ModelTransform(dict_transform)
        model = SampleModel(name="test", value=42)
        result = model_transform.eval(model)
        assert result == [{"name": True, "value": True}]

    def test_eval_with_list_of_dicts(self):
        """eval works with a list of dicts."""
        dict_transform = DictionaryTransform({"name": "test"})
        model_transform = ModelTransform(dict_transform)
        result = model_transform.eval([{"name": "test"}, {"name": "other"}])
        assert result == [{"name": True}, {"name": False}]

    def test_eval_with_list_of_models(self):
        """eval works with a list of Pydantic models."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 10})
        model_transform = ModelTransform(dict_transform)
        models = [
            SampleModel(name="a", value=15),
            SampleModel(name="b", value=5),
        ]
        result = model_transform.eval(models)
        assert result == [{"value": True}, {"value": False}]

    def test_eval_with_nested_model(self):
        """eval works with nested model data."""
        dict_transform = DictionaryTransform({"nested": {"key": "value"}})
        model_transform = ModelTransform(dict_transform)
        model = SampleModel(name="test", value=1, nested={"key": "value"})
        result = model_transform.eval(model)
        assert result == [{"nested": {"key": True}}]


class TestIntegration:
    """Integration tests for transform module."""

    def test_equality_predicate_generation(self):
        """Values are converted to equality predicates."""
        transform = DictionaryTransform({"status": "active", "count": 5})
        actual = {"status": "active", "count": 5}
        result = transform.eval(actual)
        assert result == {"status": True, "count": True}

    def test_mixed_predicates(self):
        """Mixed value and callable predicates work together."""
        transform = DictionaryTransform({
            "name": "test",
            "value": lambda x: x > 0,
        })
        actual = {"name": "test", "value": 10}
        result = transform.eval(actual)
        assert result == {"name": True, "value": True}

    def test_dotted_kwargs(self):
        """Dotted kwargs are expanded into nested structure."""
        transform = DictionaryTransform(None, **{"a.b.c": 1})
        actual = {"a": {"b": {"c": 1}}}
        result = transform.eval(actual)
        assert result == {"a": {"b": {"c": True}}}

    def test_kwargs_override_dict_values(self):
        """Kwargs override dict values for the same key."""
        transform = DictionaryTransform({"a": 1}, a=2)
        actual = {"a": 2}
        result = transform.eval(actual)
        assert result == {"a": True}

    def test_missing_actual_key(self):
        """Predicate receives Unset for missing actual keys."""
        transform = DictionaryTransform({"missing": lambda x: x is Unset})
        actual = {"other": 1}
        result = transform.eval(actual)
        assert result == {"missing": True}

    def test_map_stores_flattened_keys(self):
        """_map stores keys in flattened format."""
        transform = DictionaryTransform({"a": {"b": {"c": 1}}})
        assert "a.b.c" in transform._map
        assert len(transform._map) == 1
        assert "a" not in transform._map
