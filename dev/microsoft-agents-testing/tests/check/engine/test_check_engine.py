import pytest
from pydantic import BaseModel
from typing import Any

from microsoft_agents.testing.check.engine import CheckEngine
from microsoft_agents.testing.check.engine.types import SafeObject, resolve, Unset
from microsoft_agents.testing.check.engine.check_context import CheckContext


class SampleModel(BaseModel):
    name: str
    age: int
    email: str | None = None


class NestedModel(BaseModel):
    user: SampleModel
    active: bool


class TestCheckEngineInit:
    """Test CheckEngine initialization."""

    def test_default_fixtures(self):
        engine = CheckEngine()
        assert engine._fixtures is not None
        assert "actual" in engine._fixtures
        assert "root" in engine._fixtures
        assert "parent" in engine._fixtures

    def test_custom_fixtures(self):
        custom_fixtures = {
            "custom": lambda ctx: "custom_value",
            "actual": lambda ctx: resolve(ctx.actual),
        }
        engine = CheckEngine(fixtures=custom_fixtures)
        assert engine._fixtures == custom_fixtures
        assert "custom" in engine._fixtures


class TestCheckEngineCheckPrimitives:
    """Test CheckEngine.check with primitive values."""

    def test_equal_integers(self):
        engine = CheckEngine()
        assert engine.check(42, 42) is True

    def test_unequal_integers(self):
        engine = CheckEngine()
        assert engine.check(42, 100) is False

    def test_equal_strings(self):
        engine = CheckEngine()
        assert engine.check("hello", "hello") is True

    def test_unequal_strings(self):
        engine = CheckEngine()
        assert engine.check("hello", "world") is False

    def test_equal_floats(self):
        engine = CheckEngine()
        assert engine.check(3.14, 3.14) is True

    def test_equal_booleans(self):
        engine = CheckEngine()
        assert engine.check(True, True) is True
        assert engine.check(False, False) is True

    def test_unequal_booleans(self):
        engine = CheckEngine()
        assert engine.check(True, False) is False

    def test_none_values(self):
        engine = CheckEngine()
        assert engine.check(None, None) is True


class TestCheckEngineCheckDict:
    """Test CheckEngine.check with dictionary values."""

    def test_equal_flat_dicts(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30}
        baseline = {"name": "John", "age": 30}
        assert engine.check(actual, baseline) is True

    def test_unequal_flat_dicts(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30}
        baseline = {"name": "Jane", "age": 30}
        assert engine.check(actual, baseline) is False

    def test_nested_dicts(self):
        engine = CheckEngine()
        actual = {"user": {"name": "John", "profile": {"age": 30}}}
        baseline = {"user": {"name": "John", "profile": {"age": 30}}}
        assert engine.check(actual, baseline) is True

    def test_nested_dicts_mismatch(self):
        engine = CheckEngine()
        actual = {"user": {"name": "John", "profile": {"age": 30}}}
        baseline = {"user": {"name": "John", "profile": {"age": 25}}}
        assert engine.check(actual, baseline) is False

    def test_partial_baseline_match(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30, "email": "john@example.com"}
        baseline = {"name": "John"}  # Only check name
        assert engine.check(actual, baseline) is True


class TestCheckEngineCheckList:
    """Test CheckEngine.check with list values."""

    def test_equal_lists(self):
        engine = CheckEngine()
        actual = [1, 2, 3]
        baseline = [1, 2, 3]
        assert engine.check(actual, baseline) is True

    def test_unequal_lists(self):
        engine = CheckEngine()
        actual = [1, 2, 3]
        baseline = [1, 2, 4]
        assert engine.check(actual, baseline) is False

    def test_list_of_dicts(self):
        engine = CheckEngine()
        actual = [{"name": "John"}, {"name": "Jane"}]
        baseline = [{"name": "John"}, {"name": "Jane"}]
        assert engine.check(actual, baseline) is True

    def test_list_of_dicts_mismatch(self):
        engine = CheckEngine()
        actual = [{"name": "John"}, {"name": "Jane"}]
        baseline = [{"name": "John"}, {"name": "Bob"}]
        assert engine.check(actual, baseline) is False

    def test_nested_lists(self):
        engine = CheckEngine()
        actual = [[1, 2], [3, 4]]
        baseline = [[1, 2], [3, 4]]
        assert engine.check(actual, baseline) is True


class TestCheckEngineCallableBaseline:
    """Test CheckEngine.check with callable baselines."""

    def test_callable_returns_true(self):
        engine = CheckEngine()
        actual = {"value": 42}
        baseline = {"value": lambda actual: actual > 0}
        assert engine.check(actual, baseline) is True

    def test_callable_returns_false(self):
        engine = CheckEngine()
        actual = {"value": -5}
        baseline = {"value": lambda actual: actual > 0}
        assert engine.check(actual, baseline) is False

    def test_callable_with_tuple_result_pass(self):
        engine = CheckEngine()
        actual = {"value": 42}
        baseline = {"value": lambda actual: (actual > 0, "Value must be positive")}
        assert engine.check(actual, baseline) is True

    def test_callable_with_tuple_result_fail(self):
        engine = CheckEngine()
        actual = {"value": -5}
        baseline = {"value": lambda actual: (actual > 0, "Value must be positive")}
        assert engine.check(actual, baseline) is False

    def test_callable_at_root(self):
        engine = CheckEngine()
        actual = 42
        baseline = lambda actual: actual == 42
        assert engine.check(actual, baseline) is True

    def test_callable_with_root_fixture(self):
        engine = CheckEngine()
        actual = {"items": [1, 2, 3], "count": 3}
        baseline = {"count": lambda actual, root: actual == len(root["items"])}
        assert engine.check(actual, baseline) is True

    def test_callable_type_check(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30}
        baseline = {
            "name": lambda actual: isinstance(actual, str),
            "age": lambda actual: isinstance(actual, int) and actual > 0,
        }
        assert engine.check(actual, baseline) is True


class TestCheckEngineCheckVerbose:
    """Test CheckEngine.check_verbose method."""

    def test_verbose_pass_returns_empty_message(self):
        engine = CheckEngine()
        result, msg = engine.check_verbose({"name": "John"}, {"name": "John"})
        assert result is True
        assert msg == ""

    def test_verbose_fail_returns_message(self):
        engine = CheckEngine()
        result, msg = engine.check_verbose({"name": "John"}, {"name": "Jane"})
        assert result is False
        assert "John" in msg or "Jane" in msg

    def test_verbose_multiple_failures(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30}
        baseline = {"name": "Jane", "age": 25}
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False
        # Should contain info about both failures
        assert len(msg) > 0

    def test_verbose_nested_failure(self):
        engine = CheckEngine()
        actual = {"user": {"name": "John"}}
        baseline = {"user": {"name": "Jane"}}
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False

    def test_verbose_callable_failure_message(self):
        engine = CheckEngine()
        actual = {"value": -5}
        baseline = {"value": lambda actual: (actual > 0, "Value must be positive")}
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False
        assert "Value must be positive" in msg


class TestCheckEngineValidate:
    """Test CheckEngine.validate method."""

    def test_validate_pass(self):
        engine = CheckEngine()
        # Should not raise
        engine.validate({"name": "John"}, {"name": "John"})

    def test_validate_fail_raises_assertion(self):
        engine = CheckEngine()
        with pytest.raises(AssertionError):
            engine.validate({"name": "John"}, {"name": "Jane"})

    def test_validate_fail_message_in_assertion(self):
        engine = CheckEngine()
        with pytest.raises(AssertionError) as exc_info:
            engine.validate({"name": "John"}, {"name": "Jane"})
        assert "John" in str(exc_info.value) or "Jane" in str(exc_info.value)


class TestCheckEnginePydanticModels:
    """Test CheckEngine with Pydantic models."""

    def test_pydantic_model_as_actual(self):
        engine = CheckEngine()
        actual = SampleModel(name="John", age=30)
        baseline = {"name": "John", "age": 30}
        assert engine.check(actual, baseline) is True

    def test_pydantic_model_as_baseline(self):
        engine = CheckEngine()
        actual = {"name": "John", "age": 30}
        baseline = SampleModel(name="John", age=30)
        assert engine.check(actual, baseline) is True

    def test_pydantic_model_both(self):
        engine = CheckEngine()
        actual = SampleModel(name="John", age=30)
        baseline = SampleModel(name="John", age=30)
        assert engine.check(actual, baseline) is True

    def test_pydantic_model_mismatch(self):
        engine = CheckEngine()
        actual = SampleModel(name="John", age=30)
        baseline = {"name": "Jane", "age": 30}
        assert engine.check(actual, baseline) is False

    def test_nested_pydantic_model(self):
        engine = CheckEngine()
        actual = NestedModel(user=SampleModel(name="John", age=30), active=True)
        baseline = {"user": {"name": "John", "age": 30}, "active": True}
        assert engine.check(actual, baseline) is True


class TestCheckEngineInvoke:
    """Test CheckEngine._invoke method."""

    def test_invoke_with_actual_arg(self):
        engine = CheckEngine()
        actual = SafeObject({"value": 42})
        context = CheckContext(actual["value"], 42)
        
        def query_fn(actual):
            return actual == 42
        
        result, msg = engine._invoke(query_fn, context)
        assert result is True

    def test_invoke_with_root_arg(self):
        engine = CheckEngine()
        actual = SafeObject({"items": [1, 2, 3], "count": 3})
        context = CheckContext(actual["count"], 3)
        context.root_actual = {"items": [1, 2, 3], "count": 3}
        
        def query_fn(root):
            return root == {"items": [1, 2, 3], "count": 3}
        
        result, msg = engine._invoke(query_fn, context)
        assert result is True

    def test_invoke_unknown_arg_raises(self):
        engine = CheckEngine()
        actual = SafeObject({"value": 42})
        context = CheckContext(actual, {"value": 42})
        
        def query_fn(unknown_arg):
            return True
        
        with pytest.raises(RuntimeError) as exc_info:
            engine._invoke(query_fn, context)
        assert "Unknown argument 'unknown_arg'" in str(exc_info.value)

    def test_invoke_returns_tuple(self):
        engine = CheckEngine()
        actual = SafeObject(42)
        context = CheckContext(actual, 42)
        
        def query_fn(actual):
            return (actual == 42, "Custom message")
        
        result, msg = engine._invoke(query_fn, context)
        assert result is True
        assert msg == "Custom message"

    def test_invoke_returns_bool_with_default_message(self):
        engine = CheckEngine()
        actual = SafeObject(42)
        context = CheckContext(actual, 42)
        
        def query_fn(actual):
            return False
        
        result, msg = engine._invoke(query_fn, context)
        assert result is False
        assert "query_fn" in msg


class TestCheckEngineEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_dict(self):
        engine = CheckEngine()
        assert engine.check({}, {}) is True

    def test_empty_list(self):
        engine = CheckEngine()
        assert engine.check([], []) is True

    def test_mixed_types_in_list(self):
        engine = CheckEngine()
        actual = [1, "two", {"three": 3}, [4]]
        baseline = [1, "two", {"three": 3}, [4]]
        assert engine.check(actual, baseline) is True

    def test_deeply_nested_structure(self):
        engine = CheckEngine()
        actual = {"a": {"b": {"c": {"d": {"e": 42}}}}}
        baseline = {"a": {"b": {"c": {"d": {"e": 42}}}}}
        assert engine.check(actual, baseline) is True

    def test_deeply_nested_failure(self):
        engine = CheckEngine()
        actual = {"a": {"b": {"c": {"d": {"e": 42}}}}}
        baseline = {"a": {"b": {"c": {"d": {"e": 0}}}}}
        assert engine.check(actual, baseline) is False

    def test_callable_in_nested_list(self):
        engine = CheckEngine()
        actual = {"items": [{"value": 10}, {"value": 20}]}
        baseline = {"items": [{"value": lambda actual: actual > 0}, {"value": lambda actual: actual > 0}]}
        assert engine.check(actual, baseline) is True

    def test_unset_value_handling(self):
        engine = CheckEngine()
        actual = {"name": "John"}
        baseline = {"missing_key": Unset}
        # Accessing missing key in actual should result in Unset
        result = engine.check(actual, baseline)
        assert result is True


class TestCheckEngineCustomFixtures:
    """Test CheckEngine with custom fixtures."""

    def test_custom_fixture_in_callable(self):
        custom_fixtures = {
            "actual": lambda ctx: resolve(ctx.actual),
            "multiplier": lambda ctx: 2,
        }
        engine = CheckEngine(fixtures=custom_fixtures)
        actual = {"value": 10}
        baseline = {"value": lambda actual, multiplier: actual * multiplier == 20}
        assert engine.check(actual, baseline) is True

    def test_custom_fixture_overrides_default(self):
        custom_fixtures = {
            "actual": lambda ctx: resolve(ctx.actual) * 10,  # Modified actual
        }
        engine = CheckEngine(fixtures=custom_fixtures)
        actual = {"value": 5}
        baseline = {"value": lambda actual: actual == 50}  # 5 * 10
        assert engine.check(actual, baseline) is True