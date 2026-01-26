"""
Unit tests for the CheckEngine class.

This module tests:
- CheckEngine initialization and fixtures
- _invoke method for query functions
- _check_verbose recursive checking
- check_verbose, check, validate methods
"""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.check.engine.check_engine import CheckEngine, DEFAULT_FIXTURES
from microsoft_agents.testing.check.engine.check_context import CheckContext
from microsoft_agents.testing.check.engine.types import SafeObject


# =============================================================================
# Test Models
# =============================================================================

class Person(BaseModel):
    name: str
    age: int


class Address(BaseModel):
    city: str
    country: str


# =============================================================================
# CheckEngine Initialization Tests
# =============================================================================

class TestCheckEngineInit:
    """Test CheckEngine initialization."""
    
    def test_init_with_default_fixtures(self):
        engine = CheckEngine()
        assert engine._fixtures == DEFAULT_FIXTURES
    
    def test_init_with_custom_fixtures(self):
        custom_fixtures = {
            "custom": lambda ctx: "custom_value"
        }
        engine = CheckEngine(fixtures=custom_fixtures)
        assert engine._fixtures == custom_fixtures
    
    def test_init_with_none_uses_defaults(self):
        engine = CheckEngine(fixtures=None)
        assert engine._fixtures == DEFAULT_FIXTURES


# =============================================================================
# _invoke Method Tests
# =============================================================================

class TestCheckEngineInvoke:
    """Test the _invoke method."""
    
    def test_invoke_with_actual_fixture(self):
        engine = CheckEngine()
        actual_data = SafeObject({"name": "test"})
        context = CheckContext(actual_data, {"name": "test"})
        
        def check_actual(actual):
            return actual["name"] == "test"
        
        result, msg = engine._invoke(check_actual, context)
        assert result is True
    
    def test_invoke_with_root_fixture(self):
        engine = CheckEngine()
        actual_data = SafeObject({"nested": {"value": 42}})
        context = CheckContext(actual_data, {"nested": {"value": 42}})
        
        def check_root(root):
            return root["nested"]["value"] == 42
        
        result, msg = engine._invoke(check_root, context)
        assert result is True
    
    def test_invoke_with_tuple_return(self):
        engine = CheckEngine()
        actual_data = SafeObject({"value": 10})
        context = CheckContext(actual_data, {"value": 10})
        
        def check_with_message(actual):
            return True, "Custom success message"
        
        result, msg = engine._invoke(check_with_message, context)
        assert result is True
        assert msg == "Custom success message"
    
    def test_invoke_failure_with_tuple_return(self):
        engine = CheckEngine()
        actual_data = SafeObject({"value": 10})
        context = CheckContext(actual_data, {"value": 20})
        
        def check_with_message(actual):
            return False, "Values don't match"
        
        result, msg = engine._invoke(check_with_message, context)
        assert result is False
        assert msg == "Values don't match"
    
    def test_invoke_unknown_argument_raises(self):
        engine = CheckEngine()
        actual_data = SafeObject({})
        context = CheckContext(actual_data, {})
        
        def check_with_unknown(unknown_arg):
            return True
        
        with pytest.raises(RuntimeError, match="Unknown argument 'unknown_arg'"):
            engine._invoke(check_with_unknown, context)


# =============================================================================
# check_verbose Method Tests
# =============================================================================

class TestCheckVerbose:
    """Test the check_verbose method."""
    
    def test_check_verbose_matching_dicts(self):
        engine = CheckEngine()
        actual = {"name": "Alice", "age": 30}
        baseline = {"name": "Alice", "age": 30}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is True
        assert msg == ""
    
    def test_check_verbose_non_matching_dicts(self):
        engine = CheckEngine()
        actual = {"name": "Alice", "age": 30}
        baseline = {"name": "Bob", "age": 30}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False
        assert "do not match" in msg.lower() or "Alice" in msg
    
    def test_check_verbose_nested_dicts(self):
        engine = CheckEngine()
        actual = {"user": {"name": "Alice", "details": {"age": 30}}}
        baseline = {"user": {"name": "Alice", "details": {"age": 30}}}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_with_list(self):
        engine = CheckEngine()
        actual = {"items": [1, 2, 3]}
        baseline = {"items": [1, 2, 3]}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_list_mismatch(self):
        engine = CheckEngine()
        actual = {"items": [1, 2, 3]}
        baseline = {"items": [1, 2, 4]}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False
    
    def test_check_verbose_with_callable(self):
        engine = CheckEngine()
        actual = {"value": 42}
        baseline = {"value": lambda actual: actual > 40}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_with_callable_failure(self):
        engine = CheckEngine()
        actual = {"value": 10}
        baseline = {"value": lambda actual: actual> 40}
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False
    
    def test_check_verbose_with_pydantic_model(self):
        engine = CheckEngine()
        actual = Person(name="Alice", age=30)
        baseline = Person(name="Alice", age=30)
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_pydantic_mismatch(self):
        engine = CheckEngine()
        actual = Person(name="Alice", age=30)
        baseline = Person(name="Bob", age=30)
        
        result, msg = engine.check_verbose(actual, baseline)
        assert result is False


# =============================================================================
# check Method Tests
# =============================================================================

class TestCheck:
    """Test the check method."""
    
    def test_check_returns_true(self):
        engine = CheckEngine()
        actual = {"name": "test"}
        baseline = {"name": "test"}
        
        assert engine.check(actual, baseline) is True
    
    def test_check_returns_false(self):
        engine = CheckEngine()
        actual = {"name": "test"}
        baseline = {"name": "other"}
        
        assert engine.check(actual, baseline) is False


# =============================================================================
# validate Method Tests
# =============================================================================

class TestValidate:
    """Test the validate method."""
    
    def test_validate_passes(self):
        engine = CheckEngine()
        actual = {"name": "test"}
        baseline = {"name": "test"}
        
        # Should not raise
        engine.validate(actual, baseline)
    
    def test_validate_fails(self):
        engine = CheckEngine()
        actual = {"name": "test"}
        baseline = {"name": "other"}
        
        with pytest.raises(AssertionError):
            engine.validate(actual, baseline)


# =============================================================================
# Integration Tests
# =============================================================================

class TestCheckEngineIntegration:
    """Integration tests for CheckEngine."""
    
    def test_complex_nested_structure(self):
        engine = CheckEngine()
        actual = {
            "users": [
                {"name": "Alice", "scores": [85, 90, 88]},
                {"name": "Bob", "scores": [78, 82, 80]},
            ],
            "meta": {"count": 2}
        }
        baseline = {
            "users": [
                {"name": "Alice", "scores": [85, 90, 88]},
                {"name": "Bob", "scores": [78, 82, 80]},
            ],
            "meta": {"count": 2}
        }
        
        assert engine.check(actual, baseline) is True
    
    def test_partial_validation_with_callables(self):
        engine = CheckEngine()
        actual = {"value": 100, "status": "ok", "extra": "ignored"}
        baseline = {
            "value": lambda actual: actual >= 50,
            "status": "ok"
        }
        
        result, _ = engine.check_verbose(actual, baseline)
        assert result is True
    
    def test_custom_fixtures(self):
        custom_fixtures = {
            "actual": lambda ctx: SafeObject.resolve(ctx.actual) if hasattr(SafeObject, 'resolve') else ctx.actual,
            "custom": lambda ctx: "custom_value"
        }
        
        # Just test that custom fixtures can be provided
        engine = CheckEngine(fixtures=custom_fixtures)
        assert "custom" in engine._fixtures
