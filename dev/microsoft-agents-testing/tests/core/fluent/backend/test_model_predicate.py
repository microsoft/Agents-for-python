# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the model_predicate module."""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.backend.model_predicate import (
    ModelPredicate,
    ModelPredicateResult,
)
from microsoft_agents.testing.core.fluent.backend.transform import DictionaryTransform
from microsoft_agents.testing.core.fluent.backend.quantifier import (
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)


# ============================================================================
# ModelPredicateResult Tests
# ============================================================================

class TestModelPredicateResult:
    """Tests for the ModelPredicateResult class."""

    def test_init_with_empty_list(self):
        """Initializing with empty list creates empty result_bools."""
        result = ModelPredicateResult({}, {}, [])
        assert result.result_dicts == []
        assert result.result_bools == []

    def test_init_with_all_true(self):
        """Initializing with all True values produces True bools."""
        result = ModelPredicateResult({}, {}, [{"a": True, "b": True}])
        assert result.result_bools == [True]

    def test_init_with_all_false(self):
        """Initializing with all False values produces False bools."""
        result = ModelPredicateResult({}, {}, [{"a": False, "b": False}])
        assert result.result_bools == [False]

    def test_init_with_mixed_values(self):
        """Initializing with mixed values produces False bool."""
        result = ModelPredicateResult({}, {}, [{"a": True, "b": False}])
        assert result.result_bools == [False]

    def test_init_with_multiple_dicts(self):
        """Initializing with multiple dicts produces multiple bools."""
        result = ModelPredicateResult({}, {}, [
            {"a": True},
            {"a": False},
            {"a": True, "b": True},
        ])
        assert result.result_bools == [True, False, True]

    def test_init_with_nested_dict_all_true(self):
        """Initializing with nested dict all True produces True."""
        result = ModelPredicateResult({}, {}, [{"a": {"b": {"c": True}}}])
        assert result.result_bools == [True]

    def test_init_with_nested_dict_some_false(self):
        """Initializing with nested dict containing False produces False."""
        result = ModelPredicateResult({}, {}, [{"a": {"b": True, "c": False}}])
        assert result.result_bools == [False]

    def test_stores_result_dicts(self):
        """Result stores the original result_dicts."""
        dicts = [{"a": True}, {"b": False}]
        result = ModelPredicateResult({}, {}, dicts)
        assert result.result_dicts == dicts

    def test_truthy_with_empty_dict(self):
        """Empty dict is truthy (vacuous truth)."""
        result = ModelPredicateResult({}, {}, [{}])
        assert result.result_bools == [True]

    def test_truthy_with_truthy_values(self):
        """Non-boolean truthy values are converted."""
        result = ModelPredicateResult({}, {}, [{"a": 1, "b": "hello"}])
        assert result.result_bools == [True]

    def test_truthy_with_falsy_values(self):
        """Non-boolean falsy values are converted."""
        result = ModelPredicateResult({}, {}, [{"a": 0, "b": ""}])
        assert result.result_bools == [False]


class TestModelPredicateResultDictTransform:
    """Tests for the dict_transform property of ModelPredicateResult."""

    def test_dict_transform_stores_transform_map(self):
        """dict_transform stores the transform map from DictionaryTransform."""
        dict_transform = {"name": lambda x: x == "test", "value": lambda x: x > 0}
        result = ModelPredicateResult({}, dict_transform, [{"name": True, "value": True}])
        assert result.dict_transform == dict_transform

    def test_dict_transform_is_accessible(self):
        """dict_transform is accessible after initialization."""
        func = lambda x: x > 0
        dict_transform = {"key": func}
        result = ModelPredicateResult({}, dict_transform, [{"key": True}])
        assert "key" in result.dict_transform
        assert result.dict_transform["key"] is func

    def test_dict_transform_empty(self):
        """dict_transform can be empty."""
        result = ModelPredicateResult({}, {}, [])
        assert result.dict_transform == {}

    def test_dict_transform_with_nested_keys(self):
        """dict_transform stores flattened keys."""
        func = lambda x: x == "value"
        dict_transform = {"user.profile.name": func}
        result = ModelPredicateResult({}, dict_transform, [{"user": {"profile": {"name": True}}}])
        assert "user.profile.name" in result.dict_transform
        assert result.dict_transform["user.profile.name"] is func

    def test_dict_transform_from_model_predicate(self):
        """ModelPredicate.eval stores dict_transform in result."""
        predicate = ModelPredicate.from_args({"name": "test", "value": lambda x: x > 0})
        result = predicate.eval({"name": "test", "value": 10})
        
        assert "name" in result.dict_transform
        assert "value" in result.dict_transform
        assert callable(result.dict_transform["name"])
        assert callable(result.dict_transform["value"])

    def test_dict_transform_preserves_callables(self):
        """dict_transform preserves original callable functions."""
        def custom_check(x):
            return x == "expected"
        
        dict_transform = {"key": custom_check}
        result = ModelPredicateResult([], dict_transform, [{"key": True}])
        
        assert result.dict_transform["key"] is custom_check
        assert result.dict_transform["key"]("expected") is True
        assert result.dict_transform["key"]("other") is False


class TestModelPredicateResultSource:
    """Tests for the source property of ModelPredicateResult."""

    def test_source_stores_source_list(self):
        """source stores the original source list."""
        source = [{"name": "test", "value": 42}]
        result = ModelPredicateResult(source, {}, [{"name": True}])
        assert result.source == source

    def test_source_from_pydantic_models(self):
        """source converts Pydantic models to dicts."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        models = [TestModel(name="test", value=42)]
        result = ModelPredicateResult(models, {}, [{"name": True}])
        assert result.source == [{"name": "test", "value": 42}]

    def test_source_from_model_predicate(self):
        """ModelPredicate.eval stores source in result."""
        predicate = ModelPredicate.from_args({"name": "test"})
        source = {"name": "test", "value": 10}
        result = predicate.eval(source)
        
        assert result.source == [source]

    def test_source_multiple_items(self):
        """source stores multiple source items."""
        source = [{"name": "first"}, {"name": "second"}]
        result = ModelPredicateResult(source, {}, [{"name": True}, {"name": True}])
        assert result.source == source
        assert len(result.source) == 2


# ============================================================================
# Sample Models for Testing
# ============================================================================

class SampleModel(BaseModel):
    """A sample Pydantic model for testing."""

    name: str
    value: int
    active: bool = True


class NestedModel(BaseModel):
    """A Pydantic model with nested structure."""
    
    outer: dict


# ============================================================================
# ModelPredicate Initialization Tests
# ============================================================================

class TestModelPredicateInit:
    """Tests for ModelPredicate initialization."""

    def test_init_with_dictionary_transform(self):
        """ModelPredicate initializes with a DictionaryTransform."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        assert predicate._transform is not None

    def test_init_creates_model_transform(self):
        """ModelPredicate wraps DictionaryTransform in ModelTransform."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        assert predicate._transform is not None


# ============================================================================
# ModelPredicate.eval Tests with Dicts
# ============================================================================

class TestModelPredicateEvalWithDicts:
    """Tests for ModelPredicate.eval with dictionary sources."""

    def test_eval_single_dict_matching(self):
        """eval returns True for matching single dict."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test"})
        assert isinstance(result, ModelPredicateResult)
        assert result.result_bools == [True]

    def test_eval_single_dict_not_matching(self):
        """eval returns False for non-matching single dict."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "other"})
        assert result.result_bools == [False]

    def test_eval_list_of_dicts(self):
        """eval works with a list of dicts."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval([{"name": "test"}, {"name": "other"}])
        assert result.result_bools == [True, False]

    def test_eval_empty_list(self):
        """eval with empty list returns empty result."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval([])
        assert result.result_bools == []

    def test_eval_multiple_predicates_all_match(self):
        """eval with multiple predicates all matching."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test", "value": 42})
        assert result.result_bools == [True]

    def test_eval_multiple_predicates_partial_match(self):
        """eval returns False for partial match."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test", "value": 0})
        assert result.result_bools == [False]


# ============================================================================
# ModelPredicate.eval Tests with Pydantic Models
# ============================================================================

class TestModelPredicateEvalWithPydanticModels:
    """Tests for ModelPredicate.eval with Pydantic model sources."""

    def test_eval_pydantic_model_matching(self):
        """eval works with a matching Pydantic model."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        model = SampleModel(name="test", value=42)
        result = predicate.eval(model)
        assert result.result_bools == [True]

    def test_eval_pydantic_model_not_matching(self):
        """eval returns False for non-matching Pydantic model."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        model = SampleModel(name="other", value=42)
        result = predicate.eval(model)
        assert result.result_bools == [False]

    def test_eval_list_of_pydantic_models(self):
        """eval works with a list of Pydantic models."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 10})
        predicate = ModelPredicate(dict_transform)
        models = [
            SampleModel(name="a", value=15),
            SampleModel(name="b", value=5),
        ]
        result = predicate.eval(models)
        assert result.result_bools == [True, False]

    def test_eval_pydantic_model_with_nested_dict(self):
        """eval works with Pydantic model containing nested dict."""
        predicate = ModelPredicate.from_args({"outer": {"inner": 42}})
        model = NestedModel(outer={"inner": 42})
        result = predicate.eval(model)
        assert result.result_bools == [True]


# ============================================================================
# ModelPredicate.eval Tests with Callables
# ============================================================================

class TestModelPredicateEvalWithCallables:
    """Tests for ModelPredicate.eval with callable predicates."""

    def test_eval_with_simple_callable(self):
        """eval works with simple callable predicate."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 0})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"value": 5})
        assert result.result_bools == [True]

    def test_eval_with_callable_returning_false(self):
        """eval returns False when callable returns False."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 10})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"value": 5})
        assert result.result_bools == [False]

    def test_eval_with_root_callable(self):
        """eval works with root-level callable."""
        predicate = ModelPredicate.from_args(lambda x: x.get("value", 0) > 0)
        result = predicate.eval({"value": 10})
        assert result.result_bools == [True]

    def test_eval_with_root_callable_on_pydantic_model(self):
        """eval with root callable accesses original Pydantic model."""
        predicate = ModelPredicate.from_args(lambda x: x.value > 10)
        model = SampleModel(name="test", value=20)
        result = predicate.eval(model)
        assert result.result_bools == [True]

    def test_eval_with_root_callable_list(self):
        """eval with root callable works on list of models."""
        predicate = ModelPredicate.from_args(lambda x: x.value > 10)
        models = [
            SampleModel(name="a", value=15),
            SampleModel(name="b", value=5),
        ]
        result = predicate.eval(models)
        assert result.result_bools == [True, False]

    def test_eval_with_mixed_value_and_callable(self):
        """eval works with mixed value and callable predicates."""
        predicate = ModelPredicate.from_args(
            {"name": "test", "value": lambda x: x > 0}
        )
        result = predicate.eval({"name": "test", "value": 10})
        assert result.result_bools == [True]


# ============================================================================
# ModelPredicate.from_args Tests
# ============================================================================

class TestModelPredicateFromArgs:
    """Tests for the ModelPredicate.from_args factory method."""

    def test_from_args_with_dict(self):
        """from_args creates predicate from dict."""
        predicate = ModelPredicate.from_args({"a": 1})
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_callable(self):
        """from_args creates predicate from callable."""
        predicate = ModelPredicate.from_args(lambda x: x > 0)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_none(self):
        """from_args creates predicate from None."""
        predicate = ModelPredicate.from_args(None)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_existing_predicate(self):
        """from_args returns existing predicate unchanged."""
        original = ModelPredicate(DictionaryTransform({"a": 1}))
        result = ModelPredicate.from_args(original)
        assert result is original

    def test_from_args_with_kwargs(self):
        """from_args creates predicate with kwargs."""
        predicate = ModelPredicate.from_args(None, a=1, b=2)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_dict_and_kwargs(self):
        """from_args creates predicate merging dict and kwargs."""
        predicate = ModelPredicate.from_args({"a": 1}, b=2)
        assert isinstance(predicate, ModelPredicate)
        # Verify both are included
        result = predicate.eval({"a": 1, "b": 2})
        assert result.result_bools == [True]

    def test_from_args_kwargs_override_dict(self):
        """from_args kwargs should work alongside dict values."""
        predicate = ModelPredicate.from_args({"a": 1}, a=2)
        # kwargs should override dict value
        result = predicate.eval({"a": 2})
        assert result.result_bools == [True]


# ============================================================================
# ModelPredicate with Quantifiers Tests
# ============================================================================

class TestModelPredicateWithQuantifiers:
    """Tests demonstrating ModelPredicate results with quantifiers."""

    def test_for_all_all_true(self):
        """for_all returns True when all items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": 3}])
        assert for_all(result.result_bools) is True

    def test_for_all_some_false(self):
        """for_all returns False when any item fails."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": 1}, {"value": -1}, {"value": 3}])
        assert for_all(result.result_bools) is False

    def test_for_any_some_true(self):
        """for_any returns True when any item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert for_any(result.result_bools) is True

    def test_for_any_all_false(self):
        """for_any returns False when all items fail."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": -2}, {"value": -3}])
        assert for_any(result.result_bools) is False

    def test_for_none_all_false(self):
        """for_none returns True when all items fail predicate."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": -2}, {"value": -3}])
        assert for_none(result.result_bools) is True

    def test_for_none_some_true(self):
        """for_none returns False when any item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert for_none(result.result_bools) is False

    def test_for_one_exactly_one(self):
        """for_one returns True when exactly one item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert for_one(result.result_bools) is True

    def test_for_one_none_true(self):
        """for_one returns False when no items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": -1}, {"value": -2}, {"value": -3}])
        assert for_one(result.result_bools) is False

    def test_for_one_multiple_true(self):
        """for_one returns False when multiple items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": -3}])
        assert for_one(result.result_bools) is False

    def test_for_n_exact_count(self):
        """for_n returns True when exactly n items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": -3}])
        assert for_n(2)(result.result_bools) is True

    def test_for_n_wrong_count(self):
        """for_n returns False when count doesn't match."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0})
        result = predicate.eval([{"value": 1}, {"value": -2}, {"value": -3}])
        assert for_n(2)(result.result_bools) is False


# ============================================================================
# Nested Predicate Tests
# ============================================================================

class TestNestedPredicates:
    """Tests for nested predicate evaluation."""

    def test_nested_dict_predicate(self):
        """Nested dict predicates are evaluated correctly."""
        predicate = ModelPredicate.from_args(
            {"user": {"name": "test", "active": True}}
        )
        result = predicate.eval({"user": {"name": "test", "active": True}})
        assert result.result_bools == [True]

    def test_nested_dict_predicate_not_matching(self):
        """Nested dict predicate returns False when not matching."""
        predicate = ModelPredicate.from_args(
            {"user": {"name": "test"}}
        )
        result = predicate.eval({"user": {"name": "other"}})
        assert result.result_bools == [False]

    def test_dotted_kwargs_create_nested(self):
        """Dotted kwargs create nested predicates."""
        predicate = ModelPredicate.from_args(None, **{"a.b.c": 1})
        result = predicate.eval({"a": {"b": {"c": 1}}})
        assert result.result_bools == [True]

    def test_dotted_kwargs_with_callable(self):
        """Dotted kwargs with callable work correctly."""
        predicate = ModelPredicate.from_args(None, **{"a.b": lambda x: x > 5})
        result = predicate.eval({"a": {"b": 10}})
        assert result.result_bools == [True]


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_missing_key_in_source(self):
        """Predicate handles missing keys gracefully."""
        predicate = ModelPredicate.from_args({"missing_key": "value"})
        result = predicate.eval({"other_key": "value"})
        # Missing key should not match
        assert result.result_bools == [False]

    def test_none_predicate_matches_all(self):
        """None predicate with no kwargs matches all."""
        predicate = ModelPredicate.from_args(None)
        result = predicate.eval({"any": "data"})
        assert result.result_bools == [True]

    def test_empty_dict_predicate_matches_all(self):
        """Empty dict predicate matches all."""
        predicate = ModelPredicate.from_args({})
        result = predicate.eval({"any": "data"})
        assert result.result_bools == [True]

    def test_predicate_with_boolean_false_value(self):
        """Predicate correctly matches False boolean value."""
        predicate = ModelPredicate.from_args({"active": False})
        result = predicate.eval({"active": False})
        assert result.result_bools == [True]

    def test_predicate_with_zero_value(self):
        """Predicate correctly matches zero value."""
        predicate = ModelPredicate.from_args({"count": 0})
        result = predicate.eval({"count": 0})
        assert result.result_bools == [True]

    def test_predicate_with_empty_string(self):
        """Predicate correctly matches empty string."""
        predicate = ModelPredicate.from_args({"text": ""})
        result = predicate.eval({"text": ""})
        assert result.result_bools == [True]