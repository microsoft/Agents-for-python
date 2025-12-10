import pytest
from unittest.mock import Mock

from microsoft_agents.testing.assertions.assertions import Assertions
from microsoft_agents.testing.assertions.assertion_context import AssertionContext
from microsoft_agents.testing.assertions.types import SafeObject, DynamicObject, Unset


class TestAssertionsExpand:
    """Test the Assertions.expand method for flattening and expanding dictionaries."""
    
    def test_expand_non_dict_returns_as_is(self):
        """Test that non-dict values are returned unchanged"""
        assert Assertions.expand("string") == "string"
        assert Assertions.expand(123) == 123
        assert Assertions.expand([1, 2, 3]) == [1, 2, 3]
        assert Assertions.expand(None) is None
    
    def test_expand_flat_dict_no_dots(self):
        """Test expansion of a flat dictionary without dots in keys"""
        data = {"key1": "value1", "key2": "value2"}
        result = Assertions.expand(data)
        assert result == {"key1": "value1", "key2": "value2"}
    
    def test_expand_simple_nested_keys(self):
        """Test expansion of simple dotted keys"""
        data = {"parent.child": "value"}
        result = Assertions.expand(data)
        assert result == {"parent": {"child": "value"}}
    
    def test_expand_multiple_levels(self):
        """Test expansion of multiple nested levels"""
        data = {"root.level1.level2": "value"}
        result = Assertions.expand(data)
        assert result == {"root": {"level1": {"level2": "value"}}}
    
    def test_expand_multiple_keys_same_root(self):
        """Test expansion with multiple keys sharing the same root"""
        data = {
            "parent.child1": "value1",
            "parent.child2": "value2"
        }
        result = Assertions.expand(data)
        assert result == {
            "parent": {
                "child1": "value1",
                "child2": "value2"
            }
        }
    
    def test_expand_mixed_flat_and_nested(self):
        """Test expansion with mixed flat and nested keys"""
        data = {
            "flat_key": "flat_value",
            "nested.key": "nested_value"
        }
        result = Assertions.expand(data)
        assert result == {
            "flat_key": "flat_value",
            "nested": {"key": "nested_value"}
        }
    
    def test_expand_complex_nested_structure(self):
        """Test expansion with complex nested structure"""
        data = {
            "root.child1": "value1",
            "root.child2.grandchild": "value2",
            "other": "value3"
        }
        result = Assertions.expand(data)
        assert result == {
            "root": {
                "child1": "value1",
                "child2": {"grandchild": "value2"}
            },
            "other": "value3"
        }
    
    def test_expand_recursive_expansion(self):
        """Test that expansion is applied recursively"""
        data = {
            "level1.level2": {"level3.level4": "value"}
        }
        result = Assertions.expand(data)
        assert result == {
            "level1": {
                "level2": {
                    "level3": {"level4": "value"}
                }
            }
        }
    
    def test_expand_duplicate_root_raises_error(self):
        """Test that duplicate root keys raise RuntimeError"""
        data = {
            "root": "value1",
            "root.child": "value2"
        }
        with pytest.raises(RuntimeError):
            Assertions.expand(data)
    
    def test_expand_conflicting_structure_raises_error(self):
        """Test that conflicting structures raise RuntimeError"""
        data = {
            "parent": "value",
            "parent.child": "child_value"
        }
        with pytest.raises(RuntimeError):
            Assertions.expand(data)
    
    def test_expand_empty_dict(self):
        """Test expansion of an empty dictionary"""
        result = Assertions.expand({})
        assert result == {}


class TestAssertionsInvoke:
    """Test the Assertions.invoke method for invoking query functions."""
    
    def test_invoke_returns_tuple_with_bool_and_message(self):
        """Test that invoke properly handles functions returning (bool, str) tuple"""
        actual = SafeObject({"value": 42})
        
        def query_func(value):
            return lambda: (True, "Success message")
        
        context = AssertionContext(actual, {})
        result, message = Assertions.invoke(actual, query_func, context)
        
        assert result is True
        assert message == "Success message"
    
    def test_invoke_returns_false_tuple(self):
        """Test that invoke handles false results correctly"""
        actual = SafeObject({"value": 42})
        
        def query_func(value):
            return lambda: (False, "Failure message")
        
        context = AssertionContext(actual, {})
        result, message = Assertions.invoke(actual, query_func, context)
        
        assert result is False
        assert message == "Failure message"
    
    def test_invoke_returns_bool_only(self):
        """Test that invoke converts single bool return to tuple"""
        actual = SafeObject({"value": 42})
        
        def query_func(value):
            return lambda: True
        
        context = AssertionContext(actual, {})
        result, message = Assertions.invoke(actual, query_func, context)
        
        assert result is True
        assert "query_func" in message
    
    def test_invoke_returns_falsy_value(self):
        """Test that invoke handles falsy non-tuple values"""
        actual = SafeObject({"value": 42})
        
        def query_func(value):
            return lambda: 0
        
        context = AssertionContext(actual, {})
        result, message = Assertions.invoke(actual, query_func, context)
        
        assert result is False
        assert "query_func" in message
    
    def test_invoke_returns_truthy_value(self):
        """Test that invoke handles truthy non-tuple values"""
        actual = SafeObject({"value": 42})
        
        def query_func(value):
            return lambda: 1
        
        context = AssertionContext(actual, {})
        result, message = Assertions.invoke(actual, query_func, context)
        
        assert result is True
        assert "query_func" in message


class TestAssertionsCheckVerbose:
    """Test the Assertions._check_verbose and check_verbose methods."""
    
    def test_check_verbose_equal_primitives(self):
        """Test checking equal primitive values"""
        result, message = Assertions.check_verbose(42, 42)
        assert result is True
        assert message == ""
    
    def test_check_verbose_unequal_primitives(self):
        """Test checking unequal primitive values"""
        result, message = Assertions.check_verbose(42, 43)
        assert result is False
        assert "42" in message
        assert "43" in message
    
    def test_check_verbose_equal_strings(self):
        """Test checking equal strings"""
        result, message = Assertions.check_verbose("hello", "hello")
        assert result is True
        assert message == ""
    
    def test_check_verbose_unequal_strings(self):
        """Test checking unequal strings"""
        result, message = Assertions.check_verbose("hello", "world")
        assert result is False
        assert "hello" in message
        assert "world" in message
    
    def test_check_verbose_equal_dicts(self):
        """Test checking equal dictionaries"""
        actual = {"key": "value", "number": 42}
        baseline = {"key": "value", "number": 42}
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is True
        assert message == ""
    
    def test_check_verbose_unequal_dicts(self):
        """Test checking unequal dictionaries"""
        actual = {"key": "value1"}
        baseline = {"key": "value2"}
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is False
        assert "value1" in message
        assert "value2" in message
    
    def test_check_verbose_nested_dicts(self):
        """Test checking nested dictionaries"""
        actual = {"parent": {"child": "value1"}}
        baseline = {"parent": {"child": "value2"}}
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is False
        assert "value1" in message
        assert "value2" in message
    
    def test_check_verbose_equal_lists(self):
        """Test checking equal lists"""
        actual = [1, 2, 3]
        baseline = [1, 2, 3]
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is True
        assert message == ""
    
    def test_check_verbose_unequal_lists(self):
        """Test checking unequal lists"""
        actual = [1, 2, 3]
        baseline = [1, 2, 4]
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is False
        assert "3" in message
        assert "4" in message
    
    def test_check_verbose_nested_lists(self):
        """Test checking nested lists"""
        actual = [[1, 2], [3, 4]]
        baseline = [[1, 2], [3, 5]]
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is False
        assert "4" in message
        assert "5" in message
    
    def test_check_verbose_with_callable_baseline_passing(self):
        """Test checking with a callable baseline that passes"""
        actual = {"value": 42}
        
        def baseline_func(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: (resolve(value) == 42, "Value is 42")
        
        result, message = Assertions.check_verbose(actual, {"value": baseline_func})
        assert result is True
    
    def test_check_verbose_with_callable_baseline_failing(self):
        """Test checking with a callable baseline that fails"""
        actual = {"value": 42}
        
        def baseline_func(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: (resolve(value) == 100, "Value should be 100")
        
        result, message = Assertions.check_verbose(actual, {"value": baseline_func})
        assert result is False
        assert "Value should be 100" in message
    
    def test_check_verbose_mixed_dict_with_values_and_callables(self):
        """Test checking dict with mixed static values and callables"""
        actual = {"static": "value", "dynamic": 42}
        
        def check_dynamic(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) > 40
        
        baseline = {"static": "value", "dynamic": check_dynamic}
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_complex_nested_structure(self):
        """Test checking complex nested structures"""
        actual = {
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "coding"]
            }
        }
        baseline = {
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "coding"]
            }
        }
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is True
    
    def test_check_verbose_complex_nested_structure_with_diff(self):
        """Test checking complex nested structures with differences"""
        actual = {
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "coding"]
            }
        }
        baseline = {
            "user": {
                "name": "Jane",
                "age": 30,
                "hobbies": ["reading", "gaming"]
            }
        }
        result, message = Assertions.check_verbose(actual, baseline)
        assert result is False
        assert "John" in message or "Jane" in message


class TestAssertionsCheck:
    """Test the Assertions.check method."""
    
    def test_check_returns_true_for_equal_values(self):
        """Test that check returns True for equal values"""
        assert Assertions.check(42, 42) is True
        assert Assertions.check("test", "test") is True
        assert Assertions.check([1, 2, 3], [1, 2, 3]) is True
    
    def test_check_returns_false_for_unequal_values(self):
        """Test that check returns False for unequal values"""
        assert Assertions.check(42, 43) is False
        assert Assertions.check("test", "other") is False
        assert Assertions.check([1, 2, 3], [1, 2, 4]) is False
    
    def test_check_with_dict(self):
        """Test check with dictionary structures"""
        actual = {"key": "value"}
        baseline = {"key": "value"}
        assert Assertions.check(actual, baseline) is True
        
        baseline = {"key": "other"}
        assert Assertions.check(actual, baseline) is False
    
    def test_check_with_nested_structures(self):
        """Test check with nested structures"""
        actual = {"outer": {"inner": "value"}}
        baseline = {"outer": {"inner": "value"}}
        assert Assertions.check(actual, baseline) is True
        
        baseline = {"outer": {"inner": "other"}}
        assert Assertions.check(actual, baseline) is False
    
    def test_check_with_callable(self):
        """Test check with callable baseline"""
        actual = {"value": 42}
        
        def baseline_func(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) == 42
        
        baseline = {"value": baseline_func}
        assert Assertions.check(actual, baseline) is True


class TestAssertionsValidate:
    """Test the Assertions.validate method."""
    
    def test_validate_passes_for_equal_values(self):
        """Test that validate does not raise for equal values"""
        Assertions.validate(42, 42)
        Assertions.validate("test", "test")
        Assertions.validate([1, 2, 3], [1, 2, 3])
    
    def test_validate_raises_for_unequal_values(self):
        """Test that validate raises AssertionError for unequal values"""
        with pytest.raises(AssertionError):
            Assertions.validate(42, 43)
    
    def test_validate_raises_for_unequal_strings(self):
        """Test that validate raises AssertionError for unequal strings"""
        with pytest.raises(AssertionError) as exc_info:
            Assertions.validate("hello", "world")
        assert "hello" in str(exc_info.value) or "world" in str(exc_info.value)
    
    def test_validate_raises_for_unequal_dicts(self):
        """Test that validate raises AssertionError for unequal dicts"""
        actual = {"key": "value1"}
        baseline = {"key": "value2"}
        with pytest.raises(AssertionError) as exc_info:
            Assertions.validate(actual, baseline)
        assert "value1" in str(exc_info.value) or "value2" in str(exc_info.value)
    
    def test_validate_passes_for_complex_equal_structures(self):
        """Test that validate passes for complex equal structures"""
        actual = {
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "coding"]
            }
        }
        baseline = {
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "coding"]
            }
        }
        Assertions.validate(actual, baseline)
    
    def test_validate_raises_for_complex_unequal_structures(self):
        """Test that validate raises for complex unequal structures"""
        actual = {
            "user": {
                "name": "John",
                "age": 30
            }
        }
        baseline = {
            "user": {
                "name": "Jane",
                "age": 30
            }
        }
        with pytest.raises(AssertionError):
            Assertions.validate(actual, baseline)
    
    def test_validate_with_callable_baseline_passing(self):
        """Test validate with callable baseline that passes"""
        actual = {"value": 42}
        
        def baseline_func(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) == 42
        
        baseline = {"value": baseline_func}
        Assertions.validate(actual, baseline)
    
    def test_validate_with_callable_baseline_failing(self):
        """Test validate with callable baseline that fails"""
        actual = {"value": 42}
        
        def baseline_func(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: (resolve(value) == 100, "Expected value to be 100")
        
        baseline = {"value": baseline_func}
        with pytest.raises(AssertionError) as exc_info:
            Assertions.validate(actual, baseline)
        assert "Expected value to be 100" in str(exc_info.value)


class TestAssertionsIntegration:
    """Integration tests for Assertions class covering complex scenarios."""
    
    def test_integration_nested_dict_with_lists(self):
        """Test checking nested dicts containing lists"""
        actual = {
            "users": [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 30}
            ]
        }
        baseline = {
            "users": [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 30}
            ]
        }
        assert Assertions.check(actual, baseline) is True
    
    def test_integration_mixed_callables_and_values(self):
        """Test mixing callable checks and static values"""
        actual = {
            "id": 123,
            "name": "test",
            "score": 95
        }
        
        def check_id(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) > 0
        
        def check_score(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) >= 90
        
        baseline = {
            "id": check_id,
            "name": "test",
            "score": check_score
        }
        assert Assertions.check(actual, baseline) is True
    
    def test_integration_deep_nesting(self):
        """Test deeply nested structures"""
        actual = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "deep_value"
                    }
                }
            }
        }
        baseline = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "deep_value"
                    }
                }
            }
        }
        assert Assertions.check(actual, baseline) is True
    
    def test_integration_list_of_dicts_with_callables(self):
        """Test list of dicts with callable checks"""
        actual = [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]
        
        def check_value(value):
            from microsoft_agents.testing.assertions.types.safe_object import resolve
            return lambda: resolve(value) >= 10
        
        baseline = [
            {"value": check_value},
            {"value": check_value},
            {"value": check_value}
        ]
        assert Assertions.check(actual, baseline) is True
    
    def test_integration_empty_structures(self):
        """Test empty structures"""
        assert Assertions.check({}, {}) is True
        assert Assertions.check([], []) is True
    
    def test_integration_none_values(self):
        """Test handling of None values"""
        actual = {"key": None}
        baseline = {"key": None}
        assert Assertions.check(actual, baseline) is True
        
        baseline = {"key": "not_none"}
        assert Assertions.check(actual, baseline) is False