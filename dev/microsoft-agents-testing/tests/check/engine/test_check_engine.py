import pytest
from typing import Any
from pydantic import BaseModel

from microsoft_agents.testing.check.engine.check_engine import (
    CheckEngine,
    DEFAULT_FIXTURES,
)
from microsoft_agents.testing.check.engine.check_context import CheckContext
from microsoft_agents.testing.check.engine.types import SafeObject, resolve


# ============== Fixtures ==============

@pytest.fixture
def engine() -> CheckEngine:
    """Create a default CheckEngine instance."""
    return CheckEngine()


# ============== Test Models ==============

class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    id: int
    details: SimpleModel


# ============== Tests for __init__ ==============

class TestCheckEngineInit:
    
    def test_init_with_default_fixtures(self):
        """Test that CheckEngine initializes with default fixtures."""
        engine = CheckEngine()
        assert engine._fixtures == DEFAULT_FIXTURES

    def test_init_with_custom_fixtures(self):
        """Test that CheckEngine accepts custom fixtures."""
        custom_fixtures = {"custom": lambda ctx: "custom_value"}
        engine = CheckEngine(fixtures=custom_fixtures)
        assert engine._fixtures == custom_fixtures

    def test_init_with_none_fixtures_uses_defaults(self):
        """Test that passing None uses default fixtures."""
        engine = CheckEngine(fixtures=None)
        assert engine._fixtures == DEFAULT_FIXTURES


# ============== Tests for check() ==============

class TestCheckEngineCheck:
    
    def test_check_equal_primitives(self, engine: CheckEngine):
        """Test checking equal primitive values."""
        assert engine.check(42, 42) is True
        assert engine.check("hello", "hello") is True
        assert engine.check(3.14, 3.14) is True
        assert engine.check(True, True) is True

    def test_check_unequal_primitives(self, engine: CheckEngine):
        """Test checking unequal primitive values."""
        assert engine.check(42, 43) is False
        assert engine.check("hello", "world") is False
        assert engine.check(3.14, 2.71) is False
        assert engine.check(True, False) is False

    def test_check_equal_dicts(self, engine: CheckEngine):
        """Test checking equal dictionaries."""
        actual = {"name": "test", "value": 123}
        baseline = {"name": "test", "value": 123}
        assert engine.check(actual, baseline) is True

    def test_check_unequal_dicts(self, engine: CheckEngine):
        """Test checking unequal dictionaries."""
        actual = {"name": "test", "value": 123}
        baseline = {"name": "test", "value": 456}
        assert engine.check(actual, baseline) is False

    def test_check_equal_lists(self, engine: CheckEngine):
        """Test checking equal lists."""
        actual = [1, 2, 3]
        baseline = [1, 2, 3]
        assert engine.check(actual, baseline) is True

    def test_check_unequal_lists(self, engine: CheckEngine):
        """Test checking unequal lists."""
        actual = [1, 2, 3]
        baseline = [1, 2, 4]
        assert engine.check(actual, baseline) is False

    def test_check_nested_structures(self, engine: CheckEngine):
        """Test checking nested dictionaries and lists."""
        actual = {"items": [{"id": 1}, {"id": 2}], "count": 2}
        baseline = {"items": [{"id": 1}, {"id": 2}], "count": 2}
        assert engine.check(actual, baseline) is True

    def test_check_nested_structures_mismatch(self, engine: CheckEngine):
        """Test checking nested structures with mismatches."""
        actual = {"items": [{"id": 1}, {"id": 3}], "count": 2}
        baseline = {"items": [{"id": 1}, {"id": 2}], "count": 2}
        assert engine.check(actual, baseline) is False

    def test_check_partial_baseline(self, engine: CheckEngine):
        """Test that only baseline keys are checked (actual can have extra keys)."""
        actual = {"name": "test", "value": 123, "extra": "ignored"}
        baseline = {"name": "test", "value": 123}
        assert engine.check(actual, baseline) is True


# ============== Tests for check_verbose() ==============

class TestCheckEngineCheckVerbose:
    
    def test_check_verbose_success_returns_true_and_empty_message(self, engine: CheckEngine):
        """Test that successful check returns True and empty message."""
        result, message = engine.check_verbose({"key": "value"}, {"key": "value"})
        assert result is True
        assert message == ""

    def test_check_verbose_failure_returns_false_and_error_message(self, engine: CheckEngine):
        """Test that failed check returns False and error message."""
        result, message = engine.check_verbose({"key": "wrong"}, {"key": "value"})
        assert result is False
        assert "wrong" in message or "value" in message

    def test_check_verbose_multiple_failures(self, engine: CheckEngine):
        """Test that multiple failures are reported."""
        actual = {"a": 1, "b": 2}
        baseline = {"a": 10, "b": 20}
        result, message = engine.check_verbose(actual, baseline)
        assert result is False
        # Both mismatches should be in the message
        assert message != ""

    def test_check_verbose_nested_failure_message(self, engine: CheckEngine):
        """Test that nested failures produce meaningful messages."""
        actual = {"outer": {"inner": "wrong"}}
        baseline = {"outer": {"inner": "correct"}}
        result, message = engine.check_verbose(actual, baseline)
        assert result is False
        assert "wrong" in message or "correct" in message


# ============== Tests for Pydantic Model Support ==============

class TestCheckEnginePydanticModels:
    
    def test_check_pydantic_model_as_actual(self, engine: CheckEngine):
        """Test checking with Pydantic model as actual value."""
        actual = SimpleModel(name="test", value=42)
        baseline = {"name": "test", "value": 42}
        assert engine.check(actual, baseline) is True

    def test_check_pydantic_model_as_baseline(self, engine: CheckEngine):
        """Test checking with Pydantic model as baseline."""
        actual = {"name": "test", "value": 42}
        baseline = SimpleModel(name="test", value=42)
        assert engine.check(actual, baseline) is True

    def test_check_both_pydantic_models(self, engine: CheckEngine):
        """Test checking with both Pydantic models."""
        actual = SimpleModel(name="test", value=42)
        baseline = SimpleModel(name="test", value=42)
        assert engine.check(actual, baseline) is True

    def test_check_nested_pydantic_model(self, engine: CheckEngine):
        """Test checking with nested Pydantic models."""
        actual = NestedModel(id=1, details=SimpleModel(name="nested", value=100))
        baseline = {"id": 1, "details": {"name": "nested", "value": 100}}
        assert engine.check(actual, baseline) is True

    def test_check_pydantic_model_mismatch(self, engine: CheckEngine):
        """Test checking Pydantic model with mismatched values."""
        actual = SimpleModel(name="test", value=42)
        baseline = {"name": "test", "value": 99}
        assert engine.check(actual, baseline) is False


# ============== Tests for Callable Baselines ==============

class TestCheckEngineCallableBaselines:
    
    def test_check_with_callable_baseline_returning_true(self, engine: CheckEngine):
        """Test checking with a callable baseline that returns True."""
        actual = {"value": 42}
        baseline = {"value": lambda actual: True}
        assert engine.check(actual, baseline) is True

    def test_check_with_callable_baseline_returning_false(self, engine: CheckEngine):
        """Test checking with a callable baseline that returns False."""
        actual = {"value": 42}
        baseline = {"value": lambda actual: False}
        assert engine.check(actual, baseline) is False

    def test_check_with_callable_returning_tuple(self, engine: CheckEngine):
        """Test checking with a callable that returns (bool, message) tuple."""
        actual = {"value": 42}
        baseline = {"value": lambda actual: (True, "Custom success message")}
        assert engine.check(actual, baseline) is True

    def test_check_with_callable_returning_failure_tuple(self, engine: CheckEngine):
        """Test checking with a callable that returns failure tuple."""
        actual = {"value": 42}
        baseline = {"value": lambda actual: (False, "Custom failure message")}
        result, message = engine.check_verbose(actual, baseline)
        assert result is False


# ============== Tests for validate() ==============

class TestCheckEngineValidate:
    
    def test_validate_success_does_not_raise(self, engine: CheckEngine):
        """Test that validate does not raise on success."""
        engine.validate({"key": "value"}, {"key": "value"})  # Should not raise

    def test_validate_failure_raises_assertion_error(self, engine: CheckEngine):
        """Test that validate raises AssertionError on failure."""
        with pytest.raises(AssertionError) as exc_info:
            engine.validate({"key": "wrong"}, {"key": "expected"})
        assert "wrong" in str(exc_info.value) or "expected" in str(exc_info.value)

    def test_validate_with_pydantic_model(self, engine: CheckEngine):
        """Test validate with Pydantic model."""
        actual = SimpleModel(name="test", value=42)
        baseline = {"name": "test", "value": 42}
        engine.validate(actual, baseline)  # Should not raise

    def test_validate_nested_failure(self, engine: CheckEngine):
        """Test validate with nested structure failure."""
        actual = {"outer": {"inner": [1, 2, 3]}}
        baseline = {"outer": {"inner": [1, 2, 99]}}
        with pytest.raises(AssertionError):
            engine.validate(actual, baseline)


# ============== Tests for Edge Cases ==============

class TestCheckEngineEdgeCases:
    
    def test_check_empty_dict(self, engine: CheckEngine):
        """Test checking empty dictionaries."""
        assert engine.check({}, {}) is True

    def test_check_empty_list(self, engine: CheckEngine):
        """Test checking empty lists."""
        assert engine.check([], []) is True

    def test_check_none_values(self, engine: CheckEngine):
        """Test checking None values."""
        assert engine.check(None, None) is True
        assert engine.check({"key": None}, {"key": None}) is True

    def test_check_none_vs_value(self, engine: CheckEngine):
        """Test checking None against a value."""
        assert engine.check(None, "value") is False
        assert engine.check("value", None) is False

    def test_check_deeply_nested_structure(self, engine: CheckEngine):
        """Test checking deeply nested structures."""
        actual = {"a": {"b": {"c": {"d": {"e": 42}}}}}
        baseline = {"a": {"b": {"c": {"d": {"e": 42}}}}}
        assert engine.check(actual, baseline) is True

    def test_check_list_of_dicts(self, engine: CheckEngine):
        """Test checking list of dictionaries."""
        actual = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
        baseline = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
        assert engine.check(actual, baseline) is True

    def test_check_mixed_types_in_list(self, engine: CheckEngine):
        """Test checking lists with mixed types."""
        actual = [1, "two", {"three": 3}, [4, 5]]
        baseline = [1, "two", {"three": 3}, [4, 5]]
        assert engine.check(actual, baseline) is True


# ============== Tests for DEFAULT_FIXTURES ==============

class TestDefaultFixtures:
    
    def test_default_fixtures_actual(self):
        """Test that 'actual' fixture returns context.actual."""
        actual = SafeObject({"test": "value"})
        baseline = {"test": "value"}
        ctx = CheckContext(actual, baseline)
        assert DEFAULT_FIXTURES["actual"](ctx) == actual

    def test_default_fixtures_baseline(self):
        """Test that 'baseline' fixture returns context.baseline."""
        actual = SafeObject({"test": "value"})
        baseline = {"test": "value"}
        ctx = CheckContext(actual, baseline)
        assert DEFAULT_FIXTURES["baseline"](ctx) == baseline

    def test_default_fixtures_path(self):
        """Test that 'path' fixture returns context.path."""
        actual = SafeObject({"test": "value"})
        baseline = {"test": "value"}
        ctx = CheckContext(actual, baseline)
        assert DEFAULT_FIXTURES["path"](ctx) == []

    def test_default_fixtures_root_actual(self):
        """Test that 'root_actual' fixture returns context.root_actual."""
        actual = SafeObject({"test": "value"})
        baseline = {"test": "value"}
        ctx = CheckContext(actual, baseline)
        assert DEFAULT_FIXTURES["root_actual"](ctx) == actual

    def test_default_fixtures_root_baseline(self):
        """Test that 'root_baseline' fixture returns context.root_baseline."""
        actual = SafeObject({"test": "value"})
        baseline = {"test": "value"}
        ctx = CheckContext(actual, baseline)
        assert DEFAULT_FIXTURES["root_baseline"](ctx) == baseline