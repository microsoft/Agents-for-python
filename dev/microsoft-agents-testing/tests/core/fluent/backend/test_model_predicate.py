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


class TestModelPredicateResult:
    """Tests for the ModelPredicateResult class."""

    def test_init_with_empty_list(self):
        """Initializing with empty list creates empty result_bools."""
        result = ModelPredicateResult([])
        assert result.result_dicts == []
        assert result.result_bools == []

    def test_init_with_all_true(self):
        """Initializing with all True values produces True bools."""
        result = ModelPredicateResult([{"a": True, "b": True}])
        assert result.result_bools == [True]

    def test_init_with_all_false(self):
        """Initializing with all False values produces False bools."""
        result = ModelPredicateResult([{"a": False, "b": False}])
        assert result.result_bools == [False]

    def test_init_with_mixed_values(self):
        """Initializing with mixed values produces False bool."""
        result = ModelPredicateResult([{"a": True, "b": False}])
        assert result.result_bools == [False]

    def test_init_with_multiple_dicts(self):
        """Initializing with multiple dicts produces multiple bools."""
        result = ModelPredicateResult([
            {"a": True},
            {"a": False},
            {"a": True, "b": True},
        ])
        assert result.result_bools == [True, False, True]

    def test_init_with_nested_dict_all_true(self):
        """Initializing with nested dict all True produces True."""
        result = ModelPredicateResult([{"a": {"b": {"c": True}}}])
        assert result.result_bools == [True]

    def test_init_with_nested_dict_some_false(self):
        """Initializing with nested dict containing False produces False."""
        result = ModelPredicateResult([{"a": {"b": True, "c": False}}])
        assert result.result_bools == [False]

    def test_stores_result_dicts(self):
        """Result stores the original result_dicts."""
        dicts = [{"a": True}, {"b": False}]
        result = ModelPredicateResult(dicts)
        assert result.result_dicts == dicts

    def test_truthy_with_empty_dict(self):
        """Empty dict is truthy (vacuous truth)."""
        result = ModelPredicateResult([{}])
        assert result.result_bools == [True]

    def test_truthy_with_truthy_values(self):
        """Non-boolean truthy values are converted."""
        result = ModelPredicateResult([{"a": 1, "b": "hello"}])
        assert result.result_bools == [True]

    def test_truthy_with_falsy_values(self):
        """Non-boolean falsy values are converted."""
        result = ModelPredicateResult([{"a": 0, "b": ""}])
        assert result.result_bools == [False]


class SampleModel(BaseModel):
    """A sample Pydantic model for testing."""

    name: str
    value: int
    active: bool = True


class TestModelPredicate:
    """Tests for the ModelPredicate class."""

    def test_init(self):
        """ModelPredicate initializes with a DictionaryTransform."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        assert predicate._transform is not None
        assert predicate._quantifier is for_all

    def test_init_with_custom_quantifier(self):
        """ModelPredicate initializes with a custom quantifier."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform, quantifier=for_any)
        assert predicate._quantifier is for_any

    def test_eval_with_dict(self):
        """eval works with a dict source."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test"})
        assert isinstance(result, ModelPredicateResult)
        assert result.result_bools == [True]

    def test_eval_with_dict_failing(self):
        """eval returns False for failing predicate."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "other"})
        assert result.result_bools == [False]

    def test_eval_with_pydantic_model(self):
        """eval works with a Pydantic model."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        model = SampleModel(name="test", value=42)
        result = predicate.eval(model)
        assert result.result_bools == [True]

    def test_eval_with_list_of_dicts(self):
        """eval works with a list of dicts."""
        dict_transform = DictionaryTransform({"name": "test"})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval([{"name": "test"}, {"name": "other"}])
        assert result.result_bools == [True, False]

    def test_eval_with_list_of_models(self):
        """eval works with a list of Pydantic models."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 10})
        predicate = ModelPredicate(dict_transform)
        models = [
            SampleModel(name="a", value=15),
            SampleModel(name="b", value=5),
        ]
        result = predicate.eval(models)
        assert result.result_bools == [True, False]

    def test_eval_with_callable_predicate(self):
        """eval works with callable predicates."""
        dict_transform = DictionaryTransform({"value": lambda x: x > 0})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"value": 5})
        assert result.result_bools == [True]

    def test_eval_with_multiple_predicates(self):
        """eval evaluates multiple predicates."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test", "value": 42})
        assert result.result_bools == [True]

    def test_eval_with_partial_match(self):
        """eval returns False for partial match."""
        dict_transform = DictionaryTransform({"name": "test", "value": 42})
        predicate = ModelPredicate(dict_transform)
        result = predicate.eval({"name": "test", "value": 0})
        assert result.result_bools == [False]


class TestModelPredicateFromArgs:
    """Tests for the ModelPredicate.from_args factory method."""

    def test_from_args_with_dict(self):
        """from_args creates predicate from dict."""
        predicate = ModelPredicate.from_args({"a": 1}, for_all)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_callable(self):
        """from_args creates predicate from callable."""
        func = lambda x: x > 0
        predicate = ModelPredicate.from_args(func, for_all)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_none(self):
        """from_args creates predicate from None."""
        predicate = ModelPredicate.from_args(None, for_all)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_existing_predicate(self):
        """from_args returns existing predicate."""
        original = ModelPredicate(DictionaryTransform({"a": 1}))
        result = ModelPredicate.from_args(original, for_any)
        assert result is original

    def test_from_args_with_kwargs(self):
        """from_args creates predicate with kwargs."""
        predicate = ModelPredicate.from_args(None, for_all, a=1, b=2)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_with_dict_and_kwargs(self):
        """from_args creates predicate with dict and kwargs."""
        predicate = ModelPredicate.from_args({"a": 1}, for_all, b=2)
        assert isinstance(predicate, ModelPredicate)

    def test_from_args_preserves_quantifier(self):
        """from_args uses the provided quantifier."""
        predicate = ModelPredicate.from_args({"a": 1}, for_any)
        assert predicate._quantifier is for_any


class TestModelPredicateWithQuantifiers:
    """Tests for ModelPredicate with different quantifiers."""

    def test_for_all_all_true(self):
        """for_all returns True when all items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_all)
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": 3}])
        assert predicate._quantifier(result.result_bools) is True

    def test_for_all_some_false(self):
        """for_all returns False when any item fails."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_all)
        result = predicate.eval([{"value": 1}, {"value": -1}, {"value": 3}])
        assert predicate._quantifier(result.result_bools) is False

    def test_for_any_some_true(self):
        """for_any returns True when any item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_any)
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is True

    def test_for_any_all_false(self):
        """for_any returns False when all items fail."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_any)
        result = predicate.eval([{"value": -1}, {"value": -2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is False

    def test_for_none_all_false(self):
        """for_none returns True when all items fail."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_none)
        result = predicate.eval([{"value": -1}, {"value": -2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is True

    def test_for_none_some_true(self):
        """for_none returns False when any item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_none)
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is False

    def test_for_one_exactly_one(self):
        """for_one returns True when exactly one item passes."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_one)
        result = predicate.eval([{"value": -1}, {"value": 2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is True

    def test_for_one_multiple_true(self):
        """for_one returns False when multiple items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_one)
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is False

    def test_for_n_exact_count(self):
        """for_n returns True when exactly n items pass."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_n(2))
        result = predicate.eval([{"value": 1}, {"value": 2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is True

    def test_for_n_wrong_count(self):
        """for_n returns False when count doesn't match."""
        predicate = ModelPredicate.from_args({"value": lambda x: x > 0}, for_n(2))
        result = predicate.eval([{"value": 1}, {"value": -2}, {"value": -3}])
        assert predicate._quantifier(result.result_bools) is False


class TestIntegration:
    """Integration tests for model_predicate module."""

    def test_nested_predicate_evaluation(self):
        """Nested predicates are evaluated correctly."""
        predicate = ModelPredicate.from_args(
            {"user": {"name": "test", "active": True}},
            for_all,
        )
        result = predicate.eval({"user": {"name": "test", "active": True}})
        assert result.result_bools == [True]

    def test_mixed_predicate_types(self):
        """Mixed value and callable predicates work together."""
        predicate = ModelPredicate.from_args(
            {"name": "test", "value": lambda x: x > 0},
            for_all,
        )
        result = predicate.eval({"name": "test", "value": 10})
        assert result.result_bools == [True]

    def test_dotted_kwargs(self):
        """Dotted kwargs create nested predicates."""
        predicate = ModelPredicate.from_args(None, for_all, **{"a.b.c": 1})
        result = predicate.eval({"a": {"b": {"c": 1}}})
        assert result.result_bools == [True]

    def test_pydantic_model_with_nested(self):
        """Pydantic models with nested data work correctly."""

        class NestedModel(BaseModel):
            outer: dict

        predicate = ModelPredicate.from_args({"outer": {"inner": 42}}, for_all)
        model = NestedModel(outer={"inner": 42})
        result = predicate.eval(model)
        assert result.result_bools == [True]
