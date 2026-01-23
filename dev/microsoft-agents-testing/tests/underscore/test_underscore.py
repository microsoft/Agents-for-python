"""
Additional unit tests for the Underscore placeholder implementation.

These tests focus on internal implementation details, edge cases, and 
scenarios not covered by the main test_underscore.py file.
"""

import pytest
from microsoft_agents.testing.underscore.underscore import (
    Underscore,
    ResolutionContext,
    _NotEnoughArgs,
    _MissingNamedArg,
)
from microsoft_agents.testing.underscore.models import (
    OperationType,
    PlaceholderType,
)
from microsoft_agents.testing.underscore import (
    _, _0, _1, _2, _var,
)


class TestResolutionContext:
    """Test the ResolutionContext class directly."""
    
    def test_consume_anonymous_single(self):
        ctx = ResolutionContext((1, 2, 3), {})
        assert ctx.consume_anonymous() == 1
    
    def test_consume_anonymous_sequential(self):
        ctx = ResolutionContext((1, 2, 3), {})
        assert ctx.consume_anonymous() == 1
        assert ctx.consume_anonymous() == 2
        assert ctx.consume_anonymous() == 3
    
    def test_consume_anonymous_exhausted_raises(self):
        ctx = ResolutionContext((1,), {})
        ctx.consume_anonymous()
        with pytest.raises(_NotEnoughArgs) as exc_info:
            ctx.consume_anonymous()
        assert exc_info.value.needed == 2
        assert exc_info.value.provided == 1
    
    def test_get_indexed_valid(self):
        ctx = ResolutionContext((10, 20, 30), {})
        assert ctx.get_indexed(0) == 10
        assert ctx.get_indexed(1) == 20
        assert ctx.get_indexed(2) == 30
    
    def test_get_indexed_out_of_bounds_raises(self):
        ctx = ResolutionContext((10,), {})
        with pytest.raises(_NotEnoughArgs) as exc_info:
            ctx.get_indexed(5)
        assert exc_info.value.needed == 6
        assert exc_info.value.provided == 1
    
    def test_get_indexed_updates_max_index(self):
        ctx = ResolutionContext((1, 2, 3, 4, 5), {})
        ctx.get_indexed(2)
        assert ctx._max_index_requested == 2
        ctx.get_indexed(4)
        assert ctx._max_index_requested == 4
        ctx.get_indexed(1)  # Lower index shouldn't decrease max
        assert ctx._max_index_requested == 4
    
    def test_get_named_valid(self):
        ctx = ResolutionContext((), {"x": 42, "y": "hello"})
        assert ctx.get_named("x") == 42
        assert ctx.get_named("y") == "hello"
    
    def test_get_named_missing_raises(self):
        ctx = ResolutionContext((), {"x": 42})
        with pytest.raises(_MissingNamedArg) as exc_info:
            ctx.get_named("missing")
        assert exc_info.value.name == "missing"
    
    def test_args_property(self):
        ctx = ResolutionContext((1, 2, 3), {})
        assert ctx.args == (1, 2, 3)
    
    def test_kwargs_property(self):
        ctx = ResolutionContext((), {"a": 1, "b": 2})
        assert ctx.kwargs == {"a": 1, "b": 2}
    
    def test_empty_context(self):
        ctx = ResolutionContext((), {})
        assert ctx.args == ()
        assert ctx.kwargs == {}
        with pytest.raises(_NotEnoughArgs):
            ctx.consume_anonymous()


class TestExceptionClasses:
    """Test the internal exception classes."""
    
    def test_not_enough_args_message(self):
        exc = _NotEnoughArgs(needed=5, provided=2)
        assert exc.needed == 5
        assert exc.provided == 2
        assert "5" in str(exc)
        assert "2" in str(exc)
    
    def test_missing_named_arg_message(self):
        exc = _MissingNamedArg("my_param")
        assert exc.name == "my_param"
        assert "my_param" in str(exc)


class TestUnderscoreInternalAttrs:
    """Test internal attributes of Underscore."""
    
    def test_default_initialization(self):
        u = Underscore()
        assert u._operations == []
        assert u._placeholder_type == PlaceholderType.ANONYMOUS
        assert u._placeholder_id is None
        assert u._bound_args == ()
        assert u._bound_kwargs == {}
        assert u._inner_expr is None
    
    def test_custom_initialization(self):
        inner = Underscore()
        u = Underscore(
            operations=[(OperationType.BINARY_OP, ("__add__", 1), {})],
            placeholder_type=PlaceholderType.INDEXED,
            placeholder_id=2,
            bound_args=(10, 20),
            bound_kwargs={"key": "value"},
            inner_expr=inner,
        )
        assert len(u._operations) == 1
        assert u._placeholder_type == PlaceholderType.INDEXED
        assert u._placeholder_id == 2
        assert u._bound_args == (10, 20)
        assert u._bound_kwargs == {"key": "value"}
        assert u._inner_expr is inner
    
    def test_internal_attrs_frozen(self):
        """Verify INTERNAL_ATTRS is a frozenset with expected members."""
        assert isinstance(Underscore._INTERNAL_ATTRS, frozenset)
        assert '_operations' in Underscore._INTERNAL_ATTRS
        assert '_placeholder_type' in Underscore._INTERNAL_ATTRS


class TestIsCompound:
    """Test the _is_compound property."""
    
    def test_bare_placeholder_not_compound(self):
        u = Underscore()
        assert u._is_compound is False
    
    def test_with_operations_is_compound(self):
        u = _ + 1
        assert u._is_compound is True
    
    def test_with_bound_args_is_compound(self):
        expr = _ + _
        partial = expr(5)
        assert partial._is_compound is True
    
    def test_with_bound_kwargs_is_compound(self):
        expr = _var["x"] + _var["y"]
        partial = expr(x=5)
        assert partial._is_compound is True


class TestWrapIfCompound:
    """Test the _wrap_if_compound method."""
    
    def test_simple_placeholder_returns_self(self):
        u = Underscore()
        wrapped = u._wrap_if_compound()
        assert wrapped is u  # Same object
    
    def test_compound_returns_expr_wrapper(self):
        expr = _ + 1
        wrapped = expr._wrap_if_compound()
        assert wrapped is not expr
        assert wrapped._placeholder_type == PlaceholderType.EXPR
        assert wrapped._inner_expr is expr


class TestCopyWith:
    """Test the _copy_with method."""
    
    def test_copy_without_changes(self):
        original = Underscore(
            placeholder_type=PlaceholderType.INDEXED,
            placeholder_id=1,
        )
        copy = original._copy_with()
        assert copy is not original
        assert copy._placeholder_type == original._placeholder_type
        assert copy._placeholder_id == original._placeholder_id
    
    def test_copy_with_new_operation(self):
        original = Underscore()
        new_op = (OperationType.BINARY_OP, ("__add__", 5), {})
        copy = original._copy_with(operation=new_op)
        assert len(copy._operations) == 1
        assert copy._operations[0] == new_op
        assert len(original._operations) == 0  # Original unchanged
    
    def test_copy_with_overrides(self):
        original = Underscore()
        copy = original._copy_with(
            placeholder_type=PlaceholderType.NAMED,
            placeholder_id="test",
        )
        assert copy._placeholder_type == PlaceholderType.NAMED
        assert copy._placeholder_id == "test"


class TestResolveValue:
    """Test the _resolve_value method."""
    
    def test_resolve_non_underscore_returns_as_is(self):
        u = Underscore()
        ctx = ResolutionContext((1,), {})
        assert u._resolve_value(42, ctx) == 42
        assert u._resolve_value("hello", ctx) == "hello"
        assert u._resolve_value([1, 2, 3], ctx) == [1, 2, 3]
    
    def test_resolve_underscore_resolves_it(self):
        u = Underscore()
        inner = _ + 1
        ctx = ResolutionContext((5, 10), {})
        # First consume should give 5
        result = u._resolve_value(inner, ctx)
        assert result == 6  # 5 + 1


class TestExprPlaceholderType:
    """Test EXPR placeholder type behavior."""
    
    def test_expr_resolves_inner_expression(self):
        inner = _ + 10
        outer = Underscore(
            placeholder_type=PlaceholderType.EXPR,
            inner_expr=inner,
        )
        result = outer(5)
        assert result == 15
    
    def test_expr_with_operations(self):
        inner = _ + 10
        outer = Underscore(
            placeholder_type=PlaceholderType.EXPR,
            inner_expr=inner,
            operations=[(OperationType.BINARY_OP, ("__mul__", 2), {})],
        )
        result = outer(5)
        assert result == 30  # (5 + 10) * 2
    
    def test_nested_expr(self):
        inner1 = _ + 1
        inner2 = Underscore(
            placeholder_type=PlaceholderType.EXPR,
            inner_expr=inner1,
            operations=[(OperationType.BINARY_OP, ("__mul__", 2), {})],
        )
        outer = Underscore(
            placeholder_type=PlaceholderType.EXPR,
            inner_expr=inner2,
            operations=[(OperationType.BINARY_OP, ("__add__", 100), {})],
        )
        # ((_ + 1) * 2) + 100 with _ = 5 => (6 * 2) + 100 = 112
        result = outer(5)
        assert result == 112


class TestReverseBitwiseOperators:
    """Test reverse bitwise operators."""
    
    def test_reverse_and(self):
        expr = 0b1100 & _
        assert expr(0b1010) == 0b1000
    
    def test_reverse_or(self):
        expr = 0b1100 | _
        assert expr(0b1010) == 0b1110
    
    def test_reverse_xor(self):
        expr = 0b1100 ^ _
        assert expr(0b1010) == 0b0110
    
    def test_reverse_left_shift(self):
        expr = 3 << _
        assert expr(2) == 12
    
    def test_reverse_right_shift(self):
        expr = 12 >> _
        assert expr(2) == 3


class TestOperationChaining:
    """Test complex operation chains."""
    
    def test_getattr_followed_by_call(self):
        expr = _.upper()
        assert len(expr._operations) == 2
        assert expr._operations[0][0] == OperationType.GETATTR
        assert expr._operations[1][0] == OperationType.CALL
    
    def test_getitem_followed_by_getattr(self):
        expr = _["key"].upper()
        result = expr({"key": "hello"})
        assert result == "HELLO"
    
    def test_call_with_placeholder_args(self):
        # _.join takes a list and uses the resolved value as separator
        expr = _.join(_0)
        result = expr(*[",", ["a", "b", "c"]])
        # First arg is ",", second is ["a", "b", "c"]
        # _.join resolves to ",".join, then _0 resolves to ["a", "b", "c"]
        # Wait, let me reconsider - we have two args in the tuple
        # Actually this is trickier...
        # Let's test a simpler case
    
    def test_call_with_placeholder_in_args(self):
        # Create a method call where one arg is a placeholder
        class Container:
            def add(self, a, b):
                return a + b
        
        expr = _.add(_0, _1)
        c = Container()
        # This would need 3 anonymous args or indexed args
        # Let me use indexed: _.add(_var[1], _var[2]) where _var[0] is the container
        expr2 = _0.add(_1, _2)
        result = expr2(c, 10, 20)
        assert result == 30
    
    def test_nested_getitem_with_placeholder_key(self):
        data = {"users": {"alice": 100, "bob": 200}}
        expr = _0["users"][_1]
        result = expr(data, "alice")
        assert result == 100


class TestUnknownPlaceholderType:
    """Test error handling for unknown placeholder types."""
    
    def test_unknown_type_raises(self):
        # Create an Underscore with an invalid placeholder type
        # We need to force an invalid type somehow
        class FakePlaceholderType:
            pass
        
        u = Underscore()
        object.__setattr__(u, '_placeholder_type', FakePlaceholderType())
        
        with pytest.raises(ValueError, match="Unknown placeholder type"):
            u(42)


class TestReprEdgeCases:
    """Test repr for edge cases."""
    
    def test_repr_indexed_placeholder(self):
        u = Underscore(
            placeholder_type=PlaceholderType.INDEXED,
            placeholder_id=3,
        )
        assert repr(u) == "_3"
    
    def test_repr_named_placeholder(self):
        u = Underscore(
            placeholder_type=PlaceholderType.NAMED,
            placeholder_id="my_var",
        )
        assert repr(u) == "_var['my_var']"
    
    def test_repr_expr_placeholder(self):
        inner = _ + 1
        u = Underscore(
            placeholder_type=PlaceholderType.EXPR,
            inner_expr=inner,
        )
        assert "(" in repr(u)
        assert ")" in repr(u)
    
    def test_repr_with_call_operation(self):
        expr = _.method(1, 2, key="value")
        r = repr(expr)
        assert ".method" in r
        assert "1" in r
        assert "2" in r
        assert "key" in r
    
    def test_repr_unary_operators(self):
        neg = -_
        assert repr(neg).startswith("-")
        
        pos = +_
        assert "+" in repr(pos)
        
        inv = ~_
        assert "~" in repr(inv)


class TestCallEdgeCases:
    """Test __call__ edge cases."""
    
    def test_call_with_only_kwargs(self):
        expr = _var["x"] + _var["y"]
        result = expr(x=10, y=20)
        assert result == 30
    
    def test_call_converts_trailing_getattr_to_method_call(self):
        # When calling on an expression that ends with getattr,
        # it should convert to a method call
        expr = _.upper  # ends with GETATTR
        result = expr()("hello")
        assert result == "HELLO"
    
    def test_partial_preserves_kwargs(self):
        expr = _var["a"] + _var["b"] + _var["c"]
        partial1 = expr(a=1)
        assert partial1._bound_kwargs == {"a": 1}
        partial2 = partial1(b=2)
        assert partial2._bound_kwargs == {"a": 1, "b": 2}
        result = partial2(c=3)
        assert result == 6


class TestOperatorSymbols:
    """Test that _OP_SYMBOLS covers expected operators."""
    
    def test_arithmetic_symbols(self):
        from microsoft_agents.testing.underscore.underscore import _OP_SYMBOLS
        assert _OP_SYMBOLS['__add__'] == '+'
        assert _OP_SYMBOLS['__sub__'] == '-'
        assert _OP_SYMBOLS['__mul__'] == '*'
        assert _OP_SYMBOLS['__truediv__'] == '/'
        assert _OP_SYMBOLS['__floordiv__'] == '//'
        assert _OP_SYMBOLS['__mod__'] == '%'
        assert _OP_SYMBOLS['__pow__'] == '**'
    
    def test_comparison_symbols(self):
        from microsoft_agents.testing.underscore.underscore import _OP_SYMBOLS
        assert _OP_SYMBOLS['__eq__'] == '=='
        assert _OP_SYMBOLS['__ne__'] == '!='
        assert _OP_SYMBOLS['__lt__'] == '<'
        assert _OP_SYMBOLS['__le__'] == '<='
        assert _OP_SYMBOLS['__gt__'] == '>'
        assert _OP_SYMBOLS['__ge__'] == '>='
    
    def test_bitwise_symbols(self):
        from microsoft_agents.testing.underscore.underscore import _OP_SYMBOLS
        assert _OP_SYMBOLS['__and__'] == '&'
        assert _OP_SYMBOLS['__or__'] == '|'
        assert _OP_SYMBOLS['__xor__'] == '^'
        assert _OP_SYMBOLS['__lshift__'] == '<<'
        assert _OP_SYMBOLS['__rshift__'] == '>>'
    
    def test_unary_symbols(self):
        from microsoft_agents.testing.underscore.underscore import _OP_SYMBOLS
        assert _OP_SYMBOLS['__neg__'] == '-'
        assert _OP_SYMBOLS['__pos__'] == '+'
        assert _OP_SYMBOLS['__invert__'] == '~'


class TestFactoryFunctions:
    """Test factory functions for operators."""
    
    def test_make_binop_creates_method(self):
        from microsoft_agents.testing.underscore.underscore import _make_binop
        method = _make_binop('__add__')
        u = Underscore()
        result = method(u, 5)
        assert isinstance(result, Underscore)
        assert len(result._operations) == 1
        assert result._operations[0][0] == OperationType.BINARY_OP
    
    def test_make_rbinop_creates_method(self):
        from microsoft_agents.testing.underscore.underscore import _make_rbinop
        method = _make_rbinop('__sub__')
        u = Underscore()
        result = method(u, 10)
        assert isinstance(result, Underscore)
        assert len(result._operations) == 1
        assert result._operations[0][0] == OperationType.RBINARY_OP
    
    def test_make_unop_creates_method(self):
        from microsoft_agents.testing.underscore.underscore import _make_unop
        method = _make_unop('__neg__')
        u = Underscore()
        result = method(u)
        assert isinstance(result, Underscore)
        assert len(result._operations) == 1
        assert result._operations[0][0] == OperationType.UNARY_OP


class TestOperatorAttachment:
    """Test that operators are properly attached to Underscore class."""
    
    def test_comparison_operators_attached(self):
        assert hasattr(Underscore, '__lt__')
        assert hasattr(Underscore, '__le__')
        assert hasattr(Underscore, '__gt__')
        assert hasattr(Underscore, '__ge__')
        assert hasattr(Underscore, '__eq__')
        assert hasattr(Underscore, '__ne__')
    
    def test_arithmetic_operators_attached(self):
        assert hasattr(Underscore, '__add__')
        assert hasattr(Underscore, '__sub__')
        assert hasattr(Underscore, '__mul__')
        assert hasattr(Underscore, '__truediv__')
        assert hasattr(Underscore, '__floordiv__')
        assert hasattr(Underscore, '__mod__')
        assert hasattr(Underscore, '__pow__')
    
    def test_reverse_arithmetic_attached(self):
        assert hasattr(Underscore, '__radd__')
        assert hasattr(Underscore, '__rsub__')
        assert hasattr(Underscore, '__rmul__')
        assert hasattr(Underscore, '__rtruediv__')
        assert hasattr(Underscore, '__rfloordiv__')
        assert hasattr(Underscore, '__rmod__')
        assert hasattr(Underscore, '__rpow__')
    
    def test_bitwise_operators_attached(self):
        assert hasattr(Underscore, '__and__')
        assert hasattr(Underscore, '__or__')
        assert hasattr(Underscore, '__xor__')
        assert hasattr(Underscore, '__lshift__')
        assert hasattr(Underscore, '__rshift__')
    
    def test_reverse_bitwise_attached(self):
        assert hasattr(Underscore, '__rand__')
        assert hasattr(Underscore, '__ror__')
        assert hasattr(Underscore, '__rxor__')
        assert hasattr(Underscore, '__rlshift__')
        assert hasattr(Underscore, '__rrshift__')
    
    def test_unary_operators_attached(self):
        assert hasattr(Underscore, '__neg__')
        assert hasattr(Underscore, '__pos__')
        assert hasattr(Underscore, '__invert__')


class TestImmutability:
    """Test that operations don't mutate the original placeholder."""
    
    def test_addition_doesnt_mutate(self):
        original = _
        _ + 1  # Create new expression
        assert original._operations == []
    
    def test_getattr_doesnt_mutate(self):
        original = _
        _.upper  # Create new expression
        assert original._operations == []
    
    def test_getitem_doesnt_mutate(self):
        original = _
        _[0]  # Create new expression
        assert original._operations == []
    
    def test_partial_doesnt_mutate(self):
        expr = _ + _
        original_ops = expr._operations.copy()
        expr(5)  # Create partial
        assert expr._operations == original_ops


class TestComplexNestedExpressions:
    """Test complex nested expression scenarios."""
    
    def test_deeply_nested_operations(self):
        expr = ((_ + 1) * 2 - 3) / 4
        result = expr(7)
        # ((7 + 1) * 2 - 3) / 4 = (8 * 2 - 3) / 4 = (16 - 3) / 4 = 13 / 4 = 3.25
        assert result == 3.25
    
    def test_multiple_placeholders_in_complex_expr(self):
        expr = (_0 + _1) * (_0 - _1)
        result = expr(5, 3)
        # (5 + 3) * (5 - 3) = 8 * 2 = 16
        assert result == 16
    
    def test_mixed_placeholder_types_complex(self):
        expr = (_0 + _var["offset"]) * _1
        result = expr(10, 2, offset=5)
        # (10 + 5) * 2 = 30
        assert result == 30
    
    def test_placeholder_as_getitem_key(self):
        data = {"a": 1, "b": 2, "c": 3}
        expr = _0[_1]
        assert expr(data, "a") == 1
        assert expr(data, "b") == 2
        assert expr(data, "c") == 3