import pytest
from unittest.mock import Mock

from microsoft_agents.testing.assertions.assertion_context import AssertionContext
from microsoft_agents.testing.assertions.types import SafeObject, DynamicObject, Unset
from microsoft_agents.testing.assertions.types.safe_object import resolve, parent


class TestAssertionContextInitialization:
    """Test AssertionContext initialization."""
    
    def test_basic_initialization(self):
        """Test basic initialization with actual and baseline sources"""
        actual_data = {"key": "value"}
        baseline_data = {"key": "baseline"}
        
        actual_source = SafeObject(actual_data)
        context = AssertionContext(actual_source, baseline_data)
        
        assert context._actual_source == actual_source
        assert context._baseline_source == baseline_data
        assert context._actual == actual_source
        assert context._baseline == baseline_data
        assert context._path == ""
        assert isinstance(context._context, DynamicObject)
    
    def test_initialization_with_none_baseline(self):
        """Test initialization with None baseline source defaults to empty dict"""
        actual_source = SafeObject({"key": "value"})
        context = AssertionContext(actual_source, None)
        
        assert context._baseline_source == {}
        assert context._baseline == {}
    
    def test_initialization_with_custom_actual_and_baseline(self):
        """Test initialization with custom actual and baseline values"""
        actual_source = SafeObject({"parent": {"child": "value"}})
        baseline_source = {"parent": {"child": "baseline"}}
        
        custom_actual = SafeObject("custom_actual")
        custom_baseline = "custom_baseline"
        
        context = AssertionContext(
            actual_source,
            baseline_source,
            actual=custom_actual,
            baseline=custom_baseline
        )
        
        assert context._actual == custom_actual
        assert context._baseline == custom_baseline
        assert context._actual_source == actual_source
        assert context._baseline_source == baseline_source
    
    def test_initialization_with_custom_context(self):
        """Test initialization with custom context object"""
        actual_source = SafeObject({"key": "value"})
        baseline_source = {"key": "baseline"}
        custom_context = DynamicObject({"custom_key": "custom_value"})
        
        context = AssertionContext(
            actual_source,
            baseline_source,
            context=custom_context
        )
        
        assert context._context == custom_context
        assert resolve(context._context)["custom_key"] == "custom_value"
    
    def test_initialization_with_path(self):
        """Test initialization with a custom path"""
        actual_source = SafeObject({"key": "value"})
        baseline_source = {"key": "baseline"}
        
        context = AssertionContext(
            actual_source,
            baseline_source,
            path="parent.child"
        )
        
        assert context._path == "parent.child"
    
    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters specified"""
        actual_source = SafeObject({"root": "data"})
        baseline_source = {"root": "baseline"}
        custom_actual = SafeObject({"nested": "actual"})
        custom_baseline = {"nested": "baseline"}
        custom_context = DynamicObject({"test": True})
        custom_path = "root.nested"
        
        context = AssertionContext(
            actual_source,
            baseline_source,
            actual=custom_actual,
            baseline=custom_baseline,
            context=custom_context,
            path=custom_path
        )
        
        assert context._actual_source == actual_source
        assert context._baseline_source == baseline_source
        assert context._actual == custom_actual
        assert context._baseline == custom_baseline
        assert context._context == custom_context
        assert context._path == custom_path


class TestAssertionContextNext:
    """Test AssertionContext.next() method."""
    
    def test_next_creates_new_context_with_key(self):
        """Test that next() creates a new context for a nested key"""
        actual_data = {"user": {"name": "John", "age": 30}}
        baseline_data = {"user": {"name": "Jane", "age": 25}}
        
        actual_source = SafeObject(actual_data)
        context = AssertionContext(actual_source, baseline_data)
        
        next_context = context.next("user")
        
        assert next_context._path == "user"
        assert next_context._actual_source == actual_source
        assert next_context._baseline_source == baseline_data
    
    def test_next_updates_path_correctly(self):
        """Test that next() updates the path correctly"""
        actual_source = SafeObject({"a": {"b": {"c": "value"}}})
        baseline_source = {"a": {"b": {"c": "baseline"}}}
        
        context = AssertionContext(actual_source, baseline_source)
        
        context_a = context.next("a")
        assert context_a._path == "a"
        
        context_b = context_a.next("b")
        assert context_b._path == "a.b"
        
        context_c = context_b.next("c")
        assert context_c._path == "a.b.c"
    
    def test_next_preserves_context_object(self):
        """Test that next() preserves the context object"""
        actual_source = SafeObject({"parent": {"child": "value"}})
        baseline_source = {"parent": {"child": "baseline"}}
        custom_context = DynamicObject({"preserved": True})
        
        context = AssertionContext(
            actual_source,
            baseline_source,
            context=custom_context
        )
        
        next_context = context.next("parent")
        
        assert next_context._context == custom_context
        assert resolve(next_context._context)["preserved"] is True
    
    def test_next_with_empty_path(self):
        """Test next() when starting path is empty"""
        actual_source = SafeObject({"key": "value"})
        baseline_source = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_source, path="")
        next_context = context.next("key")
        
        assert next_context._path == "key"
    
    def test_next_with_existing_path(self):
        """Test next() when starting path is not empty"""
        actual_source = SafeObject({"a": {"b": "value"}})
        baseline_source = {"a": {"b": "baseline"}}
        
        context = AssertionContext(actual_source, baseline_source, path="existing")
        next_context = context.next("a")
        
        assert next_context._path == "existing.a"
    
    def test_next_assertion_error_when_baseline_is_none(self):
        """Test that next() raises assertion error when baseline is None"""
        actual_source = SafeObject({"key": "value"})
        
        context = AssertionContext(
            actual_source,
            baseline_source=None,
            baseline=None
        )
        
        with pytest.raises(Exception):
            context.next("key")


class TestAssertionContextResolveArgs:
    """Test AssertionContext.resolve_args() method."""
    
    def test_resolve_args_with_actual_parameter(self):
        """Test resolve_args with a function that takes 'actual' parameter"""
        actual_data = {"key": "value"}
        actual_source = SafeObject(actual_data)
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_data)
        
        def query_func(actual):
            return lambda: resolve(actual)
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result == actual_data
    
    def test_resolve_args_with_path_parameter(self):
        """Test resolve_args with a function that takes 'path' parameter"""
        actual_source = SafeObject({"key": "value"})
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_data, path="parent.child")
        
        def query_func(path):
            return lambda: path
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result == "parent.child"
    
    def test_resolve_args_with_value_parameter(self):
        """Test resolve_args with a function that takes 'value' parameter"""
        actual_source = SafeObject({"parent": {"child": "nested_value"}})
        baseline_data = {"parent": {"child": "baseline"}}
        child_value = SafeObject("specific_value")
        
        context = AssertionContext(
            actual_source,
            baseline_data,
            actual=child_value
        )
        
        def query_func(value):
            return lambda: resolve(value)
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result == "specific_value"
    
    def test_resolve_args_with_parent_parameter(self):
        """Test resolve_args with a function that takes 'parent' parameter"""
        parent_obj = SafeObject({"child": "value"})
        child_obj = SafeObject("child_value", parent_object=parent_obj)
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(
            parent_obj,
            baseline_data,
            actual=child_obj
        )
        
        def query_func(parent):
            return lambda: parent
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result == parent_obj
    
    def test_resolve_args_with_context_parameter(self):
        """Test resolve_args with a function that takes 'context' parameter"""
        actual_source = SafeObject({"key": "value"})
        baseline_data = {"key": "baseline"}
        custom_context = DynamicObject({"test_key": "test_value"})
        
        context = AssertionContext(
            actual_source,
            baseline_data,
            context=custom_context
        )
        
        def query_func(context):
            return lambda: resolve(context)["test_key"]
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result == "test_value"
    
    def test_resolve_args_with_multiple_parameters(self):
        """Test resolve_args with a function that takes multiple parameters"""
        actual_data = {"key": "value"}
        actual_source = SafeObject(actual_data)
        baseline_data = {"key": "baseline"}
        custom_context = DynamicObject({"ctx": "context_value"})
        
        context = AssertionContext(
            actual_source,
            baseline_data,
            context=custom_context,
            path="test.path"
        )
        
        def query_func(actual, path, context):
            return lambda: {
                "actual": resolve(actual),
                "path": path,
                "context": resolve(context)["ctx"]
            }
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result["actual"] == actual_data
        assert result["path"] == "test.path"
        assert result["context"] == "context_value"
    
    def test_resolve_args_preserves_function_name(self):
        """Test that resolve_args preserves the original function name"""
        actual_source = SafeObject({"key": "value"})
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_data)
        
        def my_custom_query_function(path):
            return lambda: path
        
        resolved_func = context.resolve_args(my_custom_query_function)
        
        assert resolved_func.__name__ == "my_custom_query_function"
    
    def test_resolve_args_with_unknown_parameter_raises_error(self):
        """Test that resolve_args raises RuntimeError for unknown parameters"""
        actual_source = SafeObject({"key": "value"})
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_data)
        
        def query_func(unknown_param):
            return lambda: None
        
        with pytest.raises(RuntimeError, match="Unknown argument 'unknown_param'"):
            context.resolve_args(query_func)
    
    def test_resolve_args_with_all_available_parameters(self):
        """Test resolve_args with all available parameters"""
        actual_data = {"parent": {"child": "value"}}
        actual_source = SafeObject(actual_data)
        baseline_data = {"parent": {"child": "baseline"}}
        custom_context = DynamicObject({"flag": True})
        
        parent_obj = SafeObject({"child": "child_val"})
        child_obj = SafeObject("child", parent_object=parent_obj)
        
        context = AssertionContext(
            actual_source,
            baseline_data,
            actual=child_obj,
            context=custom_context,
            path="root.parent.child"
        )
        
        def query_func(actual, path, value, parent, context):
            return lambda: {
                "actual": isinstance(actual, DynamicObject),
                "path": path,
                "value": resolve(value),
                "parent": parent,
                "context": resolve(context)["flag"]
            }
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert result["actual"] is True
        assert result["path"] == "root.parent.child"
        assert result["value"] == "child"
        assert result["parent"] == parent_obj
        assert result["context"] is True
    
    def test_resolve_args_actual_is_dynamic_object(self):
        """Test that 'actual' parameter is wrapped in DynamicObject"""
        actual_data = {"key": "value"}
        actual_source = SafeObject(actual_data)
        baseline_data = {"key": "baseline"}
        
        context = AssertionContext(actual_source, baseline_data)
        
        def query_func(actual):
            return lambda: actual
        
        resolved_func = context.resolve_args(query_func)
        result = resolved_func()
        
        assert isinstance(result, DynamicObject)
        assert resolve(result) == actual_data


class TestAssertionContextIntegration:
    """Integration tests for AssertionContext."""
    
    def test_nested_context_navigation(self):
        """Test navigating through nested contexts"""
        actual_data = {
            "user": {
                "profile": {
                    "name": "John",
                    "address": {
                        "city": "New York"
                    }
                }
            }
        }
        baseline_data = {
            "user": {
                "profile": {
                    "name": "Jane",
                    "address": {
                        "city": "Boston"
                    }
                }
            }
        }
        
        actual_source = SafeObject(actual_data)
        context = AssertionContext(actual_source, baseline_data)
        
        user_ctx = context.next("user")
        profile_ctx = user_ctx.next("profile")
        address_ctx = profile_ctx.next("address")
        
        assert address_ctx._path == "user.profile.address"
    
    def test_resolve_args_in_nested_context(self):
        """Test resolve_args works correctly in nested contexts"""
        actual_data = {"level1": {"level2": {"value": "nested"}}}
        baseline_data = {"level1": {"level2": {"value": "baseline"}}}
        
        actual_source = SafeObject(actual_data)
        context = AssertionContext(actual_source, baseline_data)
        
        nested_ctx = context.next("level1").next("level2")
        
        def query_func(path, value):
            return lambda: (path, resolve(value))
        
        resolved_func = nested_ctx.resolve_args(query_func)
        path_result, value_result = resolved_func()
        
        assert path_result == "level1.level2"
    
    def test_context_with_empty_dicts(self):
        """Test context with empty dictionaries"""
        actual_source = SafeObject({})
        baseline_data = {}
        
        context = AssertionContext(actual_source, baseline_data)
        
        assert context._actual_source == actual_source
        assert context._baseline_source == {}
        assert context._path == ""
    
    def test_context_with_complex_data_types(self):
        """Test context with lists and mixed data types"""
        actual_data = {
            "items": [1, 2, 3],
            "config": {"enabled": True, "count": 42},
            "name": "test"
        }
        baseline_data = {
            "items": [4, 5, 6],
            "config": {"enabled": False, "count": 10},
            "name": "baseline"
        }
        
        actual_source = SafeObject(actual_data)
        context = AssertionContext(actual_source, baseline_data)
        
        assert resolve(context._actual_source) == actual_data
        assert context._baseline_source == baseline_data