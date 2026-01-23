"""
Unit tests for the underscore shortcuts module.
"""

import pytest
from microsoft_agents.testing.underscore.shortcuts import (
    _,
    _0, _1, _2, _3, _4,
    _n,
    _var,
    _VarFactory,
)
from microsoft_agents.testing.underscore.underscore import Underscore
from microsoft_agents.testing.underscore.models import PlaceholderType


class TestAnonymousPlaceholder:
    """Test the anonymous placeholder _."""
    
    def test_is_underscore_instance(self):
        assert isinstance(_, Underscore)
    
    def test_is_anonymous_type(self):
        assert _._placeholder_type == PlaceholderType.ANONYMOUS
    
    def test_has_no_placeholder_id(self):
        assert _._placeholder_id is None
    
    def test_has_no_operations(self):
        assert _._operations == []
    
    def test_resolves_single_arg(self):
        assert _(42) == 42
        assert _("hello") == "hello"
    
    def test_consumes_args_in_order(self):
        expr = _ + _
        assert expr(2, 3) == 5


class TestIndexedPlaceholders:
    """Test the pre-defined indexed placeholders _0 through _4."""
    
    def test_all_are_underscore_instances(self):
        assert isinstance(_0, Underscore)
        assert isinstance(_1, Underscore)
        assert isinstance(_2, Underscore)
        assert isinstance(_3, Underscore)
        assert isinstance(_4, Underscore)
    
    def test_all_are_indexed_type(self):
        assert _0._placeholder_type == PlaceholderType.INDEXED
        assert _1._placeholder_type == PlaceholderType.INDEXED
        assert _2._placeholder_type == PlaceholderType.INDEXED
        assert _3._placeholder_type == PlaceholderType.INDEXED
        assert _4._placeholder_type == PlaceholderType.INDEXED
    
    def test_correct_placeholder_ids(self):
        assert _0._placeholder_id == 0
        assert _1._placeholder_id == 1
        assert _2._placeholder_id == 2
        assert _3._placeholder_id == 3
        assert _4._placeholder_id == 4
    
    def test_have_no_operations(self):
        assert _0._operations == []
        assert _1._operations == []
        assert _2._operations == []
        assert _3._operations == []
        assert _4._operations == []
    
    def test_resolve_correct_positional_arg(self):
        assert _0("a", "b", "c", "d", "e") == "a"
        assert _1("a", "b", "c", "d", "e") == "b"
        assert _2("a", "b", "c", "d", "e") == "c"
        assert _3("a", "b", "c", "d", "e") == "d"
        assert _4("a", "b", "c", "d", "e") == "e"
    
    def test_can_reuse_same_index(self):
        expr = _0 * _0
        assert expr(5) == 25
    
    def test_out_of_order_access(self):
        expr = _2 - _0
        assert expr(1, 2, 10) == 9  # 10 - 1


class TestIndexedPlaceholderFactory:
    """Test the _n factory function."""
    
    def test_creates_underscore_instance(self):
        p = _n(0)
        assert isinstance(p, Underscore)
    
    def test_creates_indexed_type(self):
        p = _n(5)
        assert p._placeholder_type == PlaceholderType.INDEXED
    
    def test_sets_correct_placeholder_id(self):
        assert _n(0)._placeholder_id == 0
        assert _n(5)._placeholder_id == 5
        assert _n(100)._placeholder_id == 100
    
    def test_has_no_operations(self):
        p = _n(3)
        assert p._operations == []
    
    def test_resolves_correctly(self):
        p = _n(2)
        assert p("a", "b", "c") == "c"
    
    def test_equivalent_to_predefined(self):
        # _n(0) should behave the same as _0
        expr1 = _0 + _1
        expr2 = _n(0) + _n(1)
        assert expr1(10, 20) == expr2(10, 20)
    
    def test_higher_indices(self):
        # Can create placeholders beyond _4
        p = _n(10)
        args = tuple(range(15))
        assert p(*args) == 10


class TestVarFactoryClass:
    """Test the _VarFactory class."""
    
    def test_is_instance_of_var_factory(self):
        assert isinstance(_var, _VarFactory)
    
    def test_repr(self):
        assert repr(_var) == "_var"


class TestVarFactoryIndexedPlaceholders:
    """Test creating indexed placeholders via _var[int]."""
    
    def test_creates_underscore_instance(self):
        p = _var[0]
        assert isinstance(p, Underscore)
    
    def test_creates_indexed_type(self):
        p = _var[5]
        assert p._placeholder_type == PlaceholderType.INDEXED
    
    def test_sets_correct_placeholder_id(self):
        assert _var[0]._placeholder_id == 0
        assert _var[3]._placeholder_id == 3
        assert _var[99]._placeholder_id == 99
    
    def test_resolves_correctly(self):
        p = _var[1]
        assert p("a", "b", "c") == "b"
    
    def test_equivalent_to_predefined(self):
        expr1 = _0 + _1
        expr2 = _var[0] + _var[1]
        assert expr1(5, 10) == expr2(5, 10)
    
    def test_in_expression(self):
        expr = _var[0] * _var[1] + _var[2]
        assert expr(2, 3, 4) == 10  # 2 * 3 + 4


class TestVarFactoryNamedPlaceholdersGetitem:
    """Test creating named placeholders via _var[str]."""
    
    def test_creates_underscore_instance(self):
        p = _var["name"]
        assert isinstance(p, Underscore)
    
    def test_creates_named_type(self):
        p = _var["x"]
        assert p._placeholder_type == PlaceholderType.NAMED
    
    def test_sets_correct_placeholder_id(self):
        assert _var["x"]._placeholder_id == "x"
        assert _var["my_var"]._placeholder_id == "my_var"
        assert _var["CamelCase"]._placeholder_id == "CamelCase"
    
    def test_resolves_correctly(self):
        p = _var["value"]
        assert p(value=42) == 42
    
    def test_in_expression(self):
        expr = _var["a"] + _var["b"]
        assert expr(a=10, b=20) == 30
    
    def test_with_special_string_keys(self):
        # Keys that might be edge cases
        assert _var[""]._placeholder_id == ""
        assert _var["123"]._placeholder_id == "123"
        assert _var["with space"]._placeholder_id == "with space"
        assert _var["with-dash"]._placeholder_id == "with-dash"


class TestVarFactoryNamedPlaceholdersGetattr:
    """Test creating named placeholders via _var.name attribute syntax."""
    
    def test_creates_underscore_instance(self):
        p = _var.name
        assert isinstance(p, Underscore)
    
    def test_creates_named_type(self):
        p = _var.x
        assert p._placeholder_type == PlaceholderType.NAMED
    
    def test_sets_correct_placeholder_id(self):
        assert _var.x._placeholder_id == "x"
        assert _var.my_var._placeholder_id == "my_var"
        assert _var.CamelCase._placeholder_id == "CamelCase"
    
    def test_resolves_correctly(self):
        p = _var.value
        assert p(value=42) == 42
    
    def test_in_expression(self):
        expr = _var.a + _var.b
        assert expr(a=10, b=20) == 30
    
    def test_equivalent_to_getitem(self):
        expr1 = _var["name"] + _var["value"]
        expr2 = _var.name + _var.value
        assert expr1(name=5, value=10) == expr2(name=5, value=10)
    
    def test_private_attr_raises(self):
        with pytest.raises(AttributeError) as exc_info:
            _var._private
        assert "_private" in str(exc_info.value)
    
    def test_dunder_attr_raises(self):
        with pytest.raises(AttributeError):
            _var.__dunder__


class TestVarFactoryInvalidKeys:
    """Test error handling for invalid key types."""
    
    def test_float_key_raises(self):
        with pytest.raises(TypeError) as exc_info:
            _var[3.14]
        assert "int" in str(exc_info.value)
        assert "str" in str(exc_info.value)
        assert "float" in str(exc_info.value)
    
    def test_list_key_raises(self):
        with pytest.raises(TypeError) as exc_info:
            _var[[1, 2]]
        assert "list" in str(exc_info.value)
    
    def test_tuple_key_raises(self):
        with pytest.raises(TypeError) as exc_info:
            _var[(1, 2)]
        assert "tuple" in str(exc_info.value)
    
    def test_none_key_raises(self):
        with pytest.raises(TypeError) as exc_info:
            _var[None]
        assert "NoneType" in str(exc_info.value)
    
    def test_dict_key_raises(self):
        with pytest.raises(TypeError) as exc_info:
            _var[{"a": 1}]
        assert "dict" in str(exc_info.value)


class TestMixedPlaceholderUsage:
    """Test using different placeholder types together."""
    
    def test_anonymous_and_indexed(self):
        expr = _ + _0
        # _ consumes first arg, _0 refers to first arg
        assert expr(5) == 10
    
    def test_indexed_and_named(self):
        expr = _0 * _var["scale"]
        assert expr(5, scale=2) == 10
    
    def test_all_types_together(self):
        expr = _ + _0 + _var["offset"]
        # _ consumes first (5), _0 refers to first (5), _var["offset"] = 10
        assert expr(5, offset=10) == 20
    
    def test_predefined_and_factory_mixed(self):
        expr = _0 + _var[1] + _n(2)
        assert expr(1, 2, 3) == 6


class TestPlaceholderImmutability:
    """Test that the global placeholders are not mutated by operations."""
    
    def test_anonymous_not_mutated(self):
        original_type = _._placeholder_type
        original_id = _._placeholder_id
        _ + 1  # Create expression
        assert _._placeholder_type == original_type
        assert _._placeholder_id == original_id
        assert _._operations == []
    
    def test_indexed_not_mutated(self):
        original_id = _0._placeholder_id
        _0 * 2  # Create expression
        assert _0._placeholder_id == original_id
        assert _0._operations == []
    
    def test_var_factory_creates_new_instances(self):
        p1 = _var[0]
        p2 = _var[0]
        # Each call should create a new instance
        assert p1 is not p2
        # But they should be equivalent
        assert p1._placeholder_type == p2._placeholder_type
        assert p1._placeholder_id == p2._placeholder_id
    
    def test_n_factory_creates_new_instances(self):
        p1 = _n(0)
        p2 = _n(0)
        assert p1 is not p2
        assert p1._placeholder_type == p2._placeholder_type
        assert p1._placeholder_id == p2._placeholder_id