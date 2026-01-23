"""
Unit tests for the Underscore placeholder implementation.
"""

import pytest
from microsoft_agents.testing.underscore import (
    _, _0, _1, _2, _3, _4, _n, _var,
    Underscore,
    PlaceholderType,
    PlaceholderInfo,
    get_placeholder_info,
    get_anonymous_count,
    get_indexed_placeholders,
    get_named_placeholders,
    get_required_args,
    is_placeholder,
    pipe,
)


class TestBasicArithmetic:
    """Test basic arithmetic operations with single placeholder."""
    
    def test_addition(self):
        expr = _ + 1
        assert expr(5) == 6
    
    def test_subtraction(self):
        expr = _ - 3
        assert expr(10) == 7
    
    def test_multiplication(self):
        expr = _ * 2
        assert expr(4) == 8
    
    def test_division(self):
        expr = _ / 2
        assert expr(10) == 5.0
    
    def test_floor_division(self):
        expr = _ // 3
        assert expr(10) == 3
    
    def test_modulo(self):
        expr = _ % 3
        assert expr(10) == 1
    
    def test_power(self):
        expr = _ ** 2
        assert expr(3) == 9


class TestReverseArithmetic:
    """Test reverse arithmetic (when _ is on the right side)."""
    
    def test_reverse_addition(self):
        expr = 1 + _
        assert expr(5) == 6
    
    def test_reverse_subtraction(self):
        expr = 10 - _
        assert expr(3) == 7
    
    def test_reverse_multiplication(self):
        expr = 2 * _
        assert expr(4) == 8
    
    def test_reverse_division(self):
        expr = 10 / _
        assert expr(2) == 5.0
    
    def test_reverse_floor_division(self):
        expr = 10 // _
        assert expr(3) == 3
    
    def test_reverse_modulo(self):
        expr = 10 % _
        assert expr(3) == 1
    
    def test_reverse_power(self):
        expr = 2 ** _
        assert expr(3) == 8


class TestUnaryOperators:
    """Test unary operators."""
    
    def test_negation(self):
        expr = -_
        assert expr(5) == -5
        assert expr(-3) == 3
    
    def test_positive(self):
        expr = +_
        assert expr(5) == 5
        assert expr(-3) == -3
    
    def test_invert(self):
        expr = ~_
        assert expr(0) == -1
        assert expr(5) == -6


class TestComparisonOperators:
    """Test comparison operators."""
    
    def test_less_than(self):
        expr = _ < 5
        assert expr(3) is True
        assert expr(5) is False
        assert expr(7) is False
    
    def test_less_than_or_equal(self):
        expr = _ <= 5
        assert expr(3) is True
        assert expr(5) is True
        assert expr(7) is False
    
    def test_greater_than(self):
        expr = _ > 5
        assert expr(3) is False
        assert expr(5) is False
        assert expr(7) is True
    
    def test_greater_than_or_equal(self):
        expr = _ >= 5
        assert expr(3) is False
        assert expr(5) is True
        assert expr(7) is True
    
    def test_equal(self):
        expr = _ == 5
        assert expr(5) is True
        assert expr(3) is False
    
    def test_not_equal(self):
        expr = _ != 5
        assert expr(5) is False
        assert expr(3) is True


class TestBitwiseOperators:
    """Test bitwise operators."""
    
    def test_and(self):
        expr = _ & 0b1100
        assert expr(0b1010) == 0b1000
    
    def test_or(self):
        expr = _ | 0b1100
        assert expr(0b1010) == 0b1110
    
    def test_xor(self):
        expr = _ ^ 0b1100
        assert expr(0b1010) == 0b0110
    
    def test_left_shift(self):
        expr = _ << 2
        assert expr(3) == 12
    
    def test_right_shift(self):
        expr = _ >> 2
        assert expr(12) == 3


class TestMultiplePlaceholders:
    """Test expressions with multiple anonymous placeholders."""
    
    def test_two_placeholders_addition(self):
        expr = _ + _
        assert expr(2, 5) == 7
    
    def test_two_placeholders_subtraction(self):
        expr = _ - _
        assert expr(10, 3) == 7
    
    def test_three_placeholders(self):
        expr = _ + _ + _
        assert expr(1, 2, 3) == 6
    
    def test_mixed_operations(self):
        expr = (_ + _) * _
        assert expr(1, 2, 3) == 9  # (1 + 2) * 3
    
    def test_complex_expression(self):
        expr = _ * _ + _ * _
        assert expr(2, 3, 4, 5) == 26  # 2*3 + 4*5


class TestIndexedPlaceholders:
    """Test indexed placeholders (_0, _1, etc.)."""
    
    def test_single_indexed(self):
        expr = _0 + 1
        assert expr(5) == 6
    
    def test_two_indexed(self):
        expr = _0 + _1
        assert expr(2, 3) == 5
    
    def test_reuse_same_index(self):
        # Square function
        expr = _0 * _0
        assert expr(5) == 25
    
    def test_out_of_order_indices(self):
        # Swap arguments
        expr = _1 - _0
        assert expr(3, 10) == 7  # 10 - 3
    
    def test_mixed_indexed_expression(self):
        expr = _0 + _1 * _0
        assert expr(2, 3) == 8  # 2 + 3 * 2
    
    def test_dynamic_indexed_placeholder(self):
        expr = _var[0] + _var[1]
        assert expr(2, 3) == 5
    
    def test_n_function(self):
        expr = _n(0) + _n(1)
        assert expr(2, 3) == 5


class TestNamedPlaceholders:
    """Test named placeholders."""
    
    def test_single_named(self):
        expr = _var["x"] + 1
        assert expr(x=5) == 6
    
    def test_single_named_attr_syntax(self):
        expr = _var.x + 1
        assert expr(x=5) == 6
    
    def test_two_named(self):
        expr = _var["x"] + _var["y"]
        assert expr(x=2, y=3) == 5
    
    def test_two_named_attr_syntax(self):
        expr = _var.x + _var.y
        assert expr(x=2, y=3) == 5
    
    def test_reuse_same_name(self):
        expr = _var["x"] * _var["x"]
        assert expr(x=5) == 25
    
    def test_mixed_named_and_literal(self):
        expr = _var["base"] * 2 + _var["offset"]
        assert expr(base=10, offset=5) == 25
    
    def test_string_concatenation(self):
        expr = "Hello, " + _var["name"] + "!"
        assert expr(name="World") == "Hello, World!"


class TestMixedPlaceholderTypes:
    """Test mixing different placeholder types."""
    
    def test_indexed_and_named(self):
        expr = _0 * _var["scale"]
        assert expr(5, scale=2) == 10
    
    def test_anonymous_and_indexed(self):
        # Anonymous consumes first, then indexed refers to specific position
        expr = _ + _0
        assert expr(5) == 10  # 5 + 5


class TestPartialApplication:
    """Test automatic partial application."""
    
    def test_simple_partial(self):
        expr = _ + _
        partial = expr(2)
        assert isinstance(partial, Underscore)
        assert partial(3) == 5
    
    def test_chained_partial(self):
        expr = _ + _ + _
        p1 = expr(1)
        p2 = p1(2)
        assert p2(3) == 6
    
    def test_partial_with_indexed(self):
        expr = _0 + _1
        partial = expr(2)
        assert partial(3) == 5
    
    def test_partial_with_named(self):
        expr = _var["x"] + _var["y"]
        partial = expr(x=2)
        assert partial(y=3) == 5
    
    def test_partial_mixed(self):
        expr = _0 * _var["scale"]
        partial = expr(5)
        assert partial(scale=2) == 10


class TestExpressionIsolation:
    """Test that composed expressions are properly isolated."""
    
    def test_partial_then_multiply(self):
        f = _0 + _0 - _1
        g = f(2) * -1
        # Should be (_0 + _0 - _1) * -1, not _0 + _0 - (_1 * -1)
        assert g(3) == -1  # (2 + 2 - 3) * -1 = 1 * -1 = -1
    
    def test_partial_then_add(self):
        f = _0 * _1
        g = f(2) + 10
        assert g(3) == 16  # (2 * 3) + 10
    
    def test_chained_composition(self):
        f = _0 + _1
        g = f(1) * 2
        h = g(2) + 100
        # h should resolve immediately since g(2) = (1+2)*2 = 6, then 6+100 = 106
        assert h == 106


class TestAttributeAccess:
    """Test attribute access on placeholders."""
    
    def test_simple_attribute(self):
        expr = _.upper()
        assert expr("hello") == "HELLO"
    
    def test_chained_methods(self):
        expr = _.strip().upper()
        assert expr("  hello  ") == "HELLO"
    
    def test_method_with_args(self):
        expr = _.replace("o", "0")
        assert expr("hello") == "hell0"
    
    def test_attribute_without_call(self):
        class Obj:
            x = 42
        expr = _.x
        assert expr(Obj()) == 42


class TestItemAccess:
    """Test item access on placeholders."""
    
    def test_list_index(self):
        expr = _[0]
        assert expr([1, 2, 3]) == 1
    
    def test_list_negative_index(self):
        expr = _[-1]
        assert expr([1, 2, 3]) == 3
    
    def test_dict_key(self):
        expr = _["key"]
        assert expr({"key": "value"}) == "value"
    
    def test_nested_dict_access(self):
        expr = _["outer"]["inner"]
        assert expr({"outer": {"inner": 42}}) == 42
    
    def test_getitem_after_operation(self):
        expr = (_ + _)[0]
        # [1,2] + [3,4] = [1,2,3,4], then [0] = 1
        assert expr([1, 2], [3, 4]) == 1
    
    def test_nested_access_with_indexed(self):
        data = {"data": {"value": 42}}
        expr = _0["data"]["value"]
        assert expr(data) == 42


class TestRepr:
    """Test string representation of expressions."""
    
    def test_bare_anonymous(self):
        assert repr(_) == "_"
    
    def test_bare_indexed(self):
        assert repr(_0) == "_0"
        assert repr(_1) == "_1"
    
    def test_bare_named(self):
        assert repr(_var["x"]) == "_var['x']"
    
    def test_bare_named_attr(self):
        assert repr(_var.x) == "_var['x']"
    
    def test_simple_operation(self):
        expr = _ + 1
        assert "+" in repr(expr)
        assert "1" in repr(expr)
    
    def test_binary_with_placeholder(self):
        expr = _ + _
        assert repr(expr).count("_") >= 2
    
    def test_partial_repr(self):
        expr = _ + _
        partial = expr(2)
        assert "partial" in repr(partial)
        assert "2" in repr(partial)
    
    def test_var_factory_repr(self):
        assert repr(_var) == "_var"


class TestIntrospection:
    """Test placeholder introspection functions."""
    
    def test_is_placeholder(self):
        assert is_placeholder(_) is True
        assert is_placeholder(_0) is True
        assert is_placeholder(_ + 1) is True
        assert is_placeholder(42) is False
        assert is_placeholder("hello") is False
    
    def test_get_anonymous_count(self):
        assert get_anonymous_count(_) == 1
        assert get_anonymous_count(_ + _) == 2
        assert get_anonymous_count(_ + _ * _) == 3
        assert get_anonymous_count(_0 + _1) == 0
    
    def test_get_indexed_placeholders(self):
        assert get_indexed_placeholders(_0) == {0}
        assert get_indexed_placeholders(_0 + _1) == {0, 1}
        assert get_indexed_placeholders(_0 * _0) == {0}
        assert get_indexed_placeholders(_ + _) == set()
    
    def test_get_named_placeholders(self):
        assert get_named_placeholders(_var["x"]) == {"x"}
        assert get_named_placeholders(_var["x"] + _var["y"]) == {"x", "y"}
        assert get_named_placeholders(_var["x"] * _var["x"]) == {"x"}
        assert get_named_placeholders(_ + _0) == set()
    
    def test_get_placeholder_info(self):
        expr = _0 + _1 * _var["scale"] + _
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 1
        assert info.indexed == {0, 1}
        assert info.named == {"scale"}
    
    def test_get_required_args(self):
        expr = _0 + _1 * _var["scale"]
        pos, named = get_required_args(expr)
        assert pos == 2
        assert named == {"scale"}
    
    def test_total_positional_needed(self):
        info = PlaceholderInfo(anonymous_count=3, indexed={0, 1}, named=set())
        assert info.total_positional_needed == 3
        
        info2 = PlaceholderInfo(anonymous_count=1, indexed={0, 5}, named=set())
        assert info2.total_positional_needed == 6  # max(1, 5+1)


class TestPipe:
    """Test the pipe composition helper."""
    
    def test_simple_pipe(self):
        process = pipe(_ + 1, _ * 2)
        assert process(5) == 12  # (5 + 1) * 2
    
    def test_pipe_with_builtins(self):
        process = pipe(_ + 1, str)
        assert process(5) == "6"
    
    def test_pipe_single_function(self):
        process = pipe(_ * 2)
        assert process(5) == 10
    
    def test_pipe_many_functions(self):
        process = pipe(_ + 1, _ * 2, _ - 3, _ // 2)
        # 5 -> 6 -> 12 -> 9 -> 4
        assert process(5) == 4


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_no_args_raises(self):
        expr = _ + 1
        with pytest.raises(TypeError):
            expr()
    
    def test_identity_placeholder(self):
        # Bare _ just returns the argument
        assert _(42) == 42
        assert _("hello") == "hello"
    
    def test_chained_operations_preserve_order(self):
        expr = _ + 1 - 2 * 3
        # Due to operator precedence: _ + 1 - (2 * 3) = _ + 1 - 6
        # With _ = 10: 10 + 1 - 6 = 5
        assert expr(10) == 5
    
    def test_immutability(self):
        base = _ + 1
        derived = base * 2
        # base should be unchanged
        assert base(5) == 6
        assert derived(5) == 12
    
    def test_reuse_expression(self):
        expr = _ * 2
        assert expr(3) == 6
        assert expr(4) == 8
        assert expr(5) == 10
    
    def test_var_invalid_key_type(self):
        with pytest.raises(TypeError):
            _var[3.14]  # float not allowed
    
    def test_var_private_attr(self):
        with pytest.raises(AttributeError):
            _var._private


class TestComplexScenarios:
    """Test complex real-world-like scenarios."""
    
    def test_data_transformation(self):
        # Extract and transform data
        get_name = _0["name"].upper()
        assert get_name({"name": "alice", "age": 30}) == "ALICE"
    
    def test_conditional_style_expression(self):
        # Check if value is in range using indexed placeholders
        in_range = (_0 >= 0) & (_0 <= 100)
        assert in_range(50) is True
        assert in_range(-1) is False
        assert in_range(101) is False
    
    def test_string_formatting(self):
        formatter = "Result: " + _.upper() + "!"
        assert formatter("success") == "Result: SUCCESS!"
    
    def test_list_operations(self):
        double_list = _ * 2
        assert double_list([1, 2]) == [1, 2, 1, 2]
    
    def test_numeric_pipeline(self):
        # Normalize to 0-1 range
        normalize = (_0 - _var["min"]) / (_var["max"] - _var["min"])
        result = normalize(50, min=0, max=100)
        assert result == 0.5


class TestVarFactory:
    """Test the _var factory for creating placeholders."""
    
    def test_indexed_via_var(self):
        p = _var[0]
        assert p._placeholder_type == PlaceholderType.INDEXED
        assert p._placeholder_id == 0
    
    def test_named_via_var_getitem(self):
        p = _var["name"]
        assert p._placeholder_type == PlaceholderType.NAMED
        assert p._placeholder_id == "name"
    
    def test_named_via_var_attr(self):
        p = _var.name
        assert p._placeholder_type == PlaceholderType.NAMED
        assert p._placeholder_id == "name"
    
    def test_indexed_via_var_works(self):
        expr = _var[0] + _var[1]
        assert expr(2, 3) == 5
    
    def test_named_via_var_works(self):
        expr = _var["a"] * _var["b"]
        assert expr(a=3, b=4) == 12
    
    def test_named_via_attr_works(self):
        expr = _var.a * _var.b
        assert expr(a=3, b=4) == 12
    
    def test_var_is_equivalent_to_predefined(self):
        # _var[0] should behave the same as _0
        expr1 = _0 + _1
        expr2 = _var[0] + _var[1]
        assert expr1(2, 3) == expr2(2, 3)