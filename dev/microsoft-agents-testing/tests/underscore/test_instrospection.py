"""
Unit tests for the introspection module.

These tests cover the functions that analyze Underscore expressions
to extract information about placeholders used.
"""

import pytest
from microsoft_agents.testing.underscore.instrospection import (
    get_placeholder_info,
    get_anonymous_count,
    get_indexed_placeholders,
    get_named_placeholders,
    get_required_args,
    is_placeholder,
    _collect_placeholders,
)
from microsoft_agents.testing.underscore.underscore import (
    Underscore,
    PlaceholderType,
)
from microsoft_agents.testing.underscore.models import PlaceholderInfo
from microsoft_agents.testing.underscore import (
    _, _0, _1, _2, _3, _4, _var,
)


class TestCollectPlaceholders:
    """Test the internal _collect_placeholders function."""
    
    def test_non_underscore_value_is_ignored(self):
        """Non-Underscore values should not affect placeholder info."""
        info = PlaceholderInfo(anonymous_count=0, indexed=set(), named=set())
        _collect_placeholders("not an underscore", info)
        assert info.anonymous_count == 0
        assert info.indexed == set()
        assert info.named == set()
    
    def test_collect_anonymous_placeholder(self):
        """Anonymous placeholders should increment the count."""
        info = PlaceholderInfo(anonymous_count=0, indexed=set(), named=set())
        _collect_placeholders(_, info)
        assert info.anonymous_count == 1
    
    def test_collect_indexed_placeholder(self):
        """Indexed placeholders should be added to the indexed set."""
        info = PlaceholderInfo(anonymous_count=0, indexed=set(), named=set())
        _collect_placeholders(_0, info)
        assert info.indexed == {0}
    
    def test_collect_named_placeholder(self):
        """Named placeholders should be added to the named set."""
        info = PlaceholderInfo(anonymous_count=0, indexed=set(), named=set())
        _collect_placeholders(_var["x"], info)
        assert info.named == {"x"}


class TestGetPlaceholderInfo:
    """Test the get_placeholder_info function."""
    
    def test_single_anonymous_placeholder(self):
        """A single anonymous placeholder should be counted."""
        info = get_placeholder_info(_)
        assert info.anonymous_count == 1
        assert info.indexed == set()
        assert info.named == set()
    
    def test_single_indexed_placeholder(self):
        """A single indexed placeholder should be tracked."""
        info = get_placeholder_info(_0)
        assert info.anonymous_count == 0
        assert info.indexed == {0}
        assert info.named == set()
    
    def test_single_named_placeholder(self):
        """A single named placeholder should be tracked."""
        info = get_placeholder_info(_var["name"])
        assert info.anonymous_count == 0
        assert info.indexed == set()
        assert info.named == {"name"}
    
    def test_multiple_anonymous_placeholders(self):
        """Multiple anonymous placeholders in expression."""
        expr = _ + _ * _
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 3
    
    def test_multiple_indexed_placeholders(self):
        """Multiple indexed placeholders in expression."""
        expr = _0 + _1 * _2
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1, 2}
    
    def test_duplicate_indexed_placeholders(self):
        """Same indexed placeholder used multiple times should only appear once."""
        expr = _0 + _1 * _0
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
    
    def test_multiple_named_placeholders(self):
        """Multiple named placeholders in expression."""
        expr = _var["x"] + _var["y"]
        info = get_placeholder_info(expr)
        assert info.named == {"x", "y"}
    
    def test_duplicate_named_placeholders(self):
        """Same named placeholder used multiple times should only appear once."""
        expr = _var["x"] + _var["y"] * _var["x"]
        info = get_placeholder_info(expr)
        assert info.named == {"x", "y"}
    
    def test_mixed_placeholder_types(self):
        """Expression with all placeholder types."""
        expr = _0 + _1 * _var["scale"] + _
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 1
        assert info.indexed == {0, 1}
        assert info.named == {"scale"}
    
    def test_nested_operations(self):
        """Placeholders in nested operations should be collected."""
        expr = _0[_1]  # getitem with underscore key
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
    
    def test_placeholder_in_method_call(self):
        """Placeholders in method call arguments should be collected."""
        expr = _0.format(_1, name=_var["name"])
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
        assert info.named == {"name"}
    
    def test_total_positional_needed_anonymous_only(self):
        """Total positional should equal anonymous count when no indexed."""
        expr = _ + _ + _
        info = get_placeholder_info(expr)
        assert info.total_positional_needed == 3
    
    def test_total_positional_needed_indexed_only(self):
        """Total positional should be max index + 1 when no anonymous."""
        expr = _0 + _2  # Uses indices 0 and 2, so need 3 args
        info = get_placeholder_info(expr)
        assert info.total_positional_needed == 3
    
    def test_total_positional_needed_mixed(self):
        """Total positional should be max of anonymous count and max index + 1."""
        expr = _0 + _  # 1 anonymous, max index is 0
        info = get_placeholder_info(expr)
        # max(1 anonymous, index 0 + 1 = 1) = 1
        assert info.total_positional_needed == 1
    
    def test_attribute_access_expression(self):
        """Attribute access on placeholder should work."""
        expr = _.upper
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 1
    
    def test_named_via_attribute_syntax(self):
        """Named placeholder via attribute syntax."""
        info = get_placeholder_info(_var.name)
        assert info.named == {"name"}


class TestGetAnonymousCount:
    """Test the get_anonymous_count function."""
    
    def test_no_anonymous(self):
        """Expression with no anonymous placeholders."""
        assert get_anonymous_count(_0 + _1) == 0
    
    def test_single_anonymous(self):
        """Single anonymous placeholder."""
        assert get_anonymous_count(_) == 1
    
    def test_multiple_anonymous(self):
        """Multiple anonymous placeholders."""
        assert get_anonymous_count(_ + _ * _) == 3
    
    def test_named_and_indexed_dont_count(self):
        """Named and indexed placeholders should not be counted."""
        expr = _0 + _var["x"]
        assert get_anonymous_count(expr) == 0


class TestGetIndexedPlaceholders:
    """Test the get_indexed_placeholders function."""
    
    def test_no_indexed(self):
        """Expression with no indexed placeholders."""
        assert get_indexed_placeholders(_ + _) == set()
    
    def test_single_indexed(self):
        """Single indexed placeholder."""
        assert get_indexed_placeholders(_0) == {0}
    
    def test_multiple_indexed(self):
        """Multiple indexed placeholders."""
        assert get_indexed_placeholders(_0 + _1 * _2) == {0, 1, 2}
    
    def test_duplicate_indexed(self):
        """Duplicate indexed placeholders should appear once."""
        assert get_indexed_placeholders(_0 + _1 * _0) == {0, 1}
    
    def test_non_sequential_indices(self):
        """Non-sequential indices should be tracked."""
        assert get_indexed_placeholders(_0 + _4) == {0, 4}


class TestGetNamedPlaceholders:
    """Test the get_named_placeholders function."""
    
    def test_no_named(self):
        """Expression with no named placeholders."""
        assert get_named_placeholders(_ + _0) == set()
    
    def test_single_named(self):
        """Single named placeholder."""
        assert get_named_placeholders(_var["x"]) == {"x"}
    
    def test_multiple_named(self):
        """Multiple named placeholders."""
        expr = _var["x"] + _var["y"] * _var["z"]
        assert get_named_placeholders(expr) == {"x", "y", "z"}
    
    def test_duplicate_named(self):
        """Duplicate named placeholders should appear once."""
        expr = _var["x"] + _var["y"] * _var["x"]
        assert get_named_placeholders(expr) == {"x", "y"}
    
    def test_named_via_attribute(self):
        """Named placeholders created via attribute syntax."""
        expr = _var.foo + _var.bar
        assert get_named_placeholders(expr) == {"foo", "bar"}


class TestGetRequiredArgs:
    """Test the get_required_args function."""
    
    def test_anonymous_only(self):
        """Anonymous placeholders only."""
        pos, named = get_required_args(_ + _ * _)
        assert pos == 3
        assert named == set()
    
    def test_indexed_only(self):
        """Indexed placeholders only."""
        pos, named = get_required_args(_0 + _2)
        assert pos == 3  # Need args 0, 1, 2
        assert named == set()
    
    def test_named_only(self):
        """Named placeholders only."""
        pos, named = get_required_args(_var["x"] + _var["y"])
        assert pos == 0
        assert named == {"x", "y"}
    
    def test_mixed_types(self):
        """All placeholder types."""
        expr = _0 + _1 * _var["scale"] + _
        pos, named = get_required_args(expr)
        assert pos == 2  # max(1 anonymous, index 1 + 1 = 2)
        assert named == {"scale"}
    
    def test_empty_expression(self):
        """Simple placeholder with no operations."""
        pos, named = get_required_args(_)
        assert pos == 1
        assert named == set()


class TestIsPlaceholder:
    """Test the is_placeholder function."""
    
    def test_anonymous_placeholder(self):
        """Anonymous placeholder is a placeholder."""
        assert is_placeholder(_) is True
    
    def test_indexed_placeholder(self):
        """Indexed placeholder is a placeholder."""
        assert is_placeholder(_0) is True
        assert is_placeholder(_1) is True
    
    def test_named_placeholder(self):
        """Named placeholder is a placeholder."""
        assert is_placeholder(_var["x"]) is True
        assert is_placeholder(_var.name) is True
    
    def test_expression_is_placeholder(self):
        """Complex expressions are still placeholders."""
        assert is_placeholder(_ + 1) is True
        assert is_placeholder(_0 * _1) is True
    
    def test_non_placeholder_values(self):
        """Non-Underscore values are not placeholders."""
        assert is_placeholder(None) is False
        assert is_placeholder(42) is False
        assert is_placeholder("string") is False
        assert is_placeholder([1, 2, 3]) is False
        assert is_placeholder({"key": "value"}) is False
        assert is_placeholder(lambda x: x) is False
    
    def test_underscore_class_directly(self):
        """Directly instantiated Underscore is a placeholder."""
        assert is_placeholder(Underscore()) is True


class TestComplexExpressions:
    """Test introspection with complex nested expressions."""
    
    def test_deeply_nested_expression(self):
        """Deeply nested operations should be analyzed correctly."""
        expr = ((_0 + _1) * _2).upper()
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1, 2}
    
    def test_chained_method_calls(self):
        """Chained method calls with placeholders."""
        expr = _.strip().lower().replace(_1, _2)
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 1
        assert info.indexed == {1, 2}
    
    def test_getitem_with_placeholder_key(self):
        """Getitem where the key is also a placeholder."""
        expr = _0[_1]
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
    
    def test_mixed_operations(self):
        """Mix of binary ops, getattr, getitem, and calls."""
        expr = _var["data"]["items"][_0].name + _1
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
        assert info.named == {"data"}
    
    def test_binary_operations_with_placeholders(self):
        """Binary operations where both sides are placeholders."""
        expr = _0 > _1
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1}
    
    def test_unary_operations(self):
        """Unary operations on placeholders."""
        expr = -_0
        info = get_placeholder_info(expr)
        assert info.indexed == {0}
    
    def test_placeholder_in_kwargs(self):
        """Placeholder used as keyword argument value."""
        expr = _0.method(arg=_var["value"])
        info = get_placeholder_info(expr)
        assert info.indexed == {0}
        assert info.named == {"value"}