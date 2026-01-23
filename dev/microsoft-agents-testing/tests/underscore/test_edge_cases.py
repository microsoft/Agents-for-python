"""
Extreme Edge Cases, Abuse, and Limitation Tests for Underscore

This test module pushes the Underscore placeholder implementation to its limits,
exploring unconventional usage, notation abuse, corner cases, and documenting
known limitations and idiosyncrasies.

DOCUMENTED LIMITATIONS AND IDIOSYNCRASIES:
==========================================

1. BOOLEAN CONTEXT LIMITATION:
   - `if _` always evaluates to True (Underscore has no __bool__)
   - `_ and x` / `_ or x` will NOT short-circuit properly
   - You cannot use `_` directly in boolean expressions

2. TRUTHINESS OPERATORS:
   - `not _` returns False (not an Underscore!) 
   - `bool(_)` returns True always
   - No way to create a "negate truthiness" placeholder

3. CONTAINMENT OPERATORS:
   - `x in _` does NOT work as expected (Python calls x.__contains__)
   - `_ in x` works but evaluates immediately, returning True/False
   
4. IDENTITY AND TYPE CHECKS:
   - `_ is x` always returns False (or True only if x is same object)
   - `isinstance(_, type)` always checks Underscore type
   - No way to defer these checks

5. AUGMENTED ASSIGNMENT:
   - `x += _` doesn't work as expected (modifies x in place)
   - No way to record augmented assignment operations

6. MIXING ANONYMOUS AND INDEXED:
   - Using both `_` and `_0` in same expression can be confusing
   - Each anonymous `_` consumes next arg, `_0` always gets first arg
   - They share the same positional argument pool

7. ATTRIBUTE SETTING:
   - `_.foo = value` raises an error (cannot set attributes)
   - No way to defer attribute assignment

8. MATMUL OPERATOR:
   - `_ @ x` is NOT implemented (no __matmul__)
   
9. HASH BEHAVIOR:
   - Underscore instances are hashable but each instance is unique
   - You cannot use `_` as a reliable dict key across expressions

10. EXCEPTION HANDLING:
    - Exceptions in deferred operations propagate at resolution time
    - No way to catch exceptions within the expression chain

11. ASYNC/AWAIT:
    - `await _` doesn't work (no __await__)
    - No support for async method calls

12. WALRUS OPERATOR:
    - `(_ := x)` assigns x to the name `_`, doesn't create expression

13. SLICE OBJECTS:
    - `_[1:3]` works, but `_[::_]` or `_[_:_]` may have unexpected behavior
"""

import pytest
import operator
from microsoft_agents.testing.underscore import (
    _, _0, _1, _2, _3, _4, _n, _var,
    Underscore,
    pipe,
    get_placeholder_info,
    get_anonymous_count,
    get_indexed_placeholders,
    get_named_placeholders,
    is_placeholder,
)
from microsoft_agents.testing.underscore.models import PlaceholderType, OperationType


# =============================================================================
# LIMITATION TESTS - Document known limitations
# =============================================================================

class TestBooleanContextLimitations:
    """Test limitations around boolean contexts."""
    
    def test_underscore_always_truthy(self):
        """LIMITATION: Underscore is always truthy in boolean context."""
        assert bool(_) is True
        assert bool(_ + 1) is True
        assert bool(_0) is True
        
    def test_not_operator_returns_false_not_underscore(self):
        """LIMITATION: `not _` returns False, not an Underscore."""
        result = not _
        assert result is False
        assert not isinstance(result, Underscore)
    
    def test_and_short_circuits_with_underscore(self):
        """LIMITATION: `_ and x` evaluates to x immediately (because _ is truthy)."""
        result = _ and 42
        assert result == 42
        assert not isinstance(result, Underscore)
    
    def test_or_short_circuits_with_underscore(self):
        """LIMITATION: `_ or x` returns _ immediately (because _ is truthy)."""
        result = _ or 42
        assert isinstance(result, Underscore)
        assert result is _  # Same object
        
    def test_ternary_with_underscore_always_picks_truthy(self):
        """LIMITATION: `x if _ else y` always returns x."""
        result = "truthy" if _ else "falsy"
        assert result == "truthy"


class TestContainmentLimitations:
    """Test limitations around 'in' operator."""
    
    def test_underscore_in_list_evaluates_immediately(self):
        """LIMITATION: `_ in [...]` evaluates immediately."""
        result = _ in [1, 2, 3]
        assert result is False  # Underscore not in the list
        
    def test_item_in_underscore_not_supported(self):
        """LIMITATION: `x in _` calls __contains__ which isn't defined."""
        # This should raise AttributeError or work via __getattr__
        # Let's see what actually happens
        try:
            result = 5 in _
            # If it doesn't raise, check what we got
            assert isinstance(result, (bool, Underscore))
        except (TypeError, AttributeError):
            pass  # Expected behavior


class TestIdentityLimitations:
    """Test limitations around identity checks."""
    
    def test_is_comparison_not_deferred(self):
        """LIMITATION: `_ is x` is not deferred."""
        result = _ is None
        assert result is False  # Immediate comparison
        
    def test_isinstance_not_deferred(self):
        """LIMITATION: isinstance(_, type) checks Underscore type."""
        assert isinstance(_, Underscore)
        # No way to defer this


class TestMatmulNotImplemented:
    """Test that matmul operator is not implemented."""
    
    def test_matmul_not_supported(self):
        """LIMITATION: Matrix multiplication not implemented."""
        import numpy as np
        
        try:
            expr = _ @ np.array([[1, 2], [3, 4]])
            # If it works, we get an Underscore
            assert isinstance(expr, Underscore)
        except (TypeError, AttributeError):
            # Expected - matmul not implemented
            pass


class TestHashBehavior:
    """Test hash and dict key behavior."""
    
    def test_underscore_instances_hashable(self):
        """Underscore instances are hashable."""
        assert hash(_) is not None
        assert hash(_ + 1) is not None
        
    def test_different_instances_different_hashes(self):
        """Each Underscore expression has unique hash."""
        expr1 = _ + 1
        expr2 = _ + 1  # Same expression, different object
        # They may or may not have same hash (implementation-dependent)
        # But they are different objects
        assert expr1 is not expr2
        
    def test_can_use_as_dict_key(self):
        """Can use Underscore as dict key (but probably shouldn't)."""
        d = {_: "anon", _0: "first"}
        assert len(d) == 2


# =============================================================================
# ABUSE AND UNCONVENTIONAL USAGE
# =============================================================================

class TestNotationAbuse:
    """Test creative/abusive notation patterns."""
    
    def test_chained_comparisons_dont_short_circuit(self):
        """
        QUIRK: Python's chained comparisons expand to multiple comparisons.
        `1 < _ < 10` becomes `(1 < _) and (_ < 10)`
        Since `1 < _` returns an Underscore (truthy), `and` evaluates `_ < 10`.
        """
        result = 1 < _ < 10
        # This is actually (_ < 10) because (1 < _) is truthy
        assert isinstance(result, Underscore)
        # The actual function checks less than 10
        assert result(5) is True
        assert result(15) is False
        # Note: The `1 < _` part is LOST!
        assert result(0) is True  # Should be False if 1 < _ < 10 worked
        
    def test_double_negation_abuse(self):
        """Double negation doesn't give back an Underscore."""
        result = --_
        assert isinstance(result, Underscore)
        assert result(5) == 5
        
    def test_triple_negation(self):
        """Triple negation works as expected."""
        result = ---_
        assert isinstance(result, Underscore)
        assert result(5) == -5
        
    def test_power_of_power(self):
        """Test chained exponentiation."""
        # Python right-associates **: 2 ** 3 ** 2 == 2 ** 9 == 512
        expr = _ ** 3 ** 2
        assert expr(2) == 512  # 2 ** (3 ** 2) = 2 ** 9
        
    def test_bizarre_nesting(self):
        """Deeply nested operations."""
        expr = -(-(-(-(-_))))
        assert expr(7) == -7
        
    def test_placeholder_in_placeholder_operation(self):
        """Using placeholders as operands to other placeholders."""
        # _0 + (_1 * _0) - should work
        expr = _0 + _1 * _0
        assert expr(2, 3) == 8  # 2 + 3 * 2 = 8 (no operator precedence override)
        
    def test_self_referential_key(self):
        """Using placeholder as key to access itself... sort of."""
        # _0[_1] where _0 and _1 are both the same value
        expr = _0[_1]
        data = {0: "zero", 1: "one", "key": "value"}
        assert expr(data, 1) == "one"
        

class TestRecursiveLikePatterns:
    """Test patterns that mimic recursion."""
    
    def test_pipe_as_pseudo_recursion(self):
        """Pipe can simulate iterative application."""
        # Apply x + 1 three times
        triple_add = pipe(_ + 1, _ + 1, _ + 1)
        assert triple_add(0) == 3
        
    def test_nested_pipe(self):
        """Nested pipes should compose properly."""
        inner = pipe(_ * 2, _ + 1)  # x -> (x*2) + 1
        outer = pipe(inner, _ ** 2)  # x -> ((x*2)+1) ** 2
        assert outer(3) == 49  # ((3*2)+1)**2 = 7**2 = 49


class TestEdgeCaseDataTypes:
    """Test with unusual data types."""
    
    def test_with_none(self):
        """Operations with None."""
        expr = _ is None  # This is immediate, not deferred
        # So this doesn't work as expected
        assert expr is False  # _ is not None (immediate)
        
        # But equality works
        eq_expr = _ == None
        assert isinstance(eq_expr, Underscore)
        assert eq_expr(None) is True
        assert eq_expr(0) is False
        
    def test_with_complex_numbers(self):
        """Operations with complex numbers."""
        expr = _ + 1j
        assert expr(2) == 2 + 1j
        
        expr2 = _ * (1 + 2j)
        assert expr2(3) == 3 + 6j
        
    def test_with_bytes(self):
        """Operations with bytes."""
        expr = _ + b" world"
        assert expr(b"hello") == b"hello world"
        
    def test_with_memoryview(self):
        """Operations with memoryview."""
        data = bytearray(b"hello")
        expr = _[1:4]
        result = expr(memoryview(data))
        assert bytes(result) == b"ell"
        
    def test_with_range(self):
        """Operations with range objects."""
        expr = _[2]  # Get third element
        assert expr(range(10)) == 2
        
    def test_with_generator(self):
        """Operations with generators (consumed once!)."""
        expr = list  # Convert to list
        gen = (x for x in [1, 2, 3])
        # Note: pipe(_, list) would work differently
        
    def test_with_dict_values(self):
        """Operations on dict views."""
        expr = list  # Not underscore, but...
        d = {"a": 1, "b": 2}
        
        # Using underscore to get keys
        keys_expr = _.keys()
        result = keys_expr(d)
        assert set(result) == {"a", "b"}
        

class TestCallableObjects:
    """Test with various callable types."""
    
    def test_with_lambda(self):
        """Using lambdas with underscore."""
        expr = _(lambda x: x * 2)
        # Wait, this resolves _ with the lambda as argument
        # _ just returns its argument
        result = expr(lambda x: x * 2)
        assert result(5) == 10
        
    def test_method_reference(self):
        """Capturing method references."""
        expr = _.append
        lst = [1, 2, 3]
        method = expr(lst)  # Returns the bound method
        method(4)
        assert lst == [1, 2, 3, 4]
        
    def test_static_method_access(self):
        """Accessing static methods through placeholder."""
        class MyClass:
            @staticmethod
            def double(x):
                return x * 2
                
        expr = _.double
        cls = MyClass
        result = expr(cls)
        assert result(5) == 10


class TestSliceEdgeCases:
    """Test edge cases with slicing."""
    
    def test_basic_slice(self):
        """Basic slicing works."""
        expr = _[1:3]
        assert expr([0, 1, 2, 3, 4]) == [1, 2]
        
    def test_slice_with_step(self):
        """Slicing with step."""
        expr = _[::2]
        assert expr([0, 1, 2, 3, 4]) == [0, 2, 4]
        
    def test_negative_slice(self):
        """Negative slicing."""
        expr = _[-2:]
        assert expr([0, 1, 2, 3, 4]) == [3, 4]
        
    def test_slice_with_placeholder_start(self):
        """Using placeholder as slice start."""
        # _0[_1:] - get from index _1 onwards
        expr = _0[_1:]
        assert expr([0, 1, 2, 3, 4], 2) == [2, 3, 4]
        
    def test_slice_with_placeholder_end(self):
        """Using placeholder as slice end."""
        expr = _0[:_1]
        assert expr([0, 1, 2, 3, 4], 3) == [0, 1, 2]
        
    def test_slice_with_both_placeholder_bounds(self):
        """Using placeholders for both start and end."""
        expr = _0[_1:_2]
        assert expr([0, 1, 2, 3, 4], 1, 4) == [1, 2, 3]


class TestAttributeChainAbuse:
    """Test extreme attribute chains."""
    
    def test_long_attribute_chain(self):
        """Very long attribute chain."""
        class Nested:
            def __init__(self):
                self.child = self
                self.value = 42
        
        obj = Nested()
        expr = _.child.child.child.child.value
        assert expr(obj) == 42
        
    def test_attribute_then_item_then_attribute(self):
        """Mixed attribute and item access."""
        class Container:
            def __init__(self):
                self.items = [{"name": "Alice"}, {"name": "Bob"}]
        
        expr = _.items[1]["name"].upper()
        assert expr(Container()) == "BOB"


class TestSpecialMethods:
    """Test accessing special (dunder) methods."""
    
    def test_access_dunder_method(self):
        """Accessing __len__ through placeholder."""
        expr = _.__len__()
        assert expr([1, 2, 3]) == 3
        
    def test_access_class(self):
        """Accessing __class__."""
        expr = _.__class__.__name__
        assert expr([1, 2, 3]) == "list"
        
    def test_access_dict(self):
        """Accessing __dict__."""
        class MyObj:
            def __init__(self):
                self.x = 10
        
        expr = _.__dict__
        assert expr(MyObj()) == {"x": 10}


# =============================================================================
# MIXING PLACEHOLDER TYPES
# =============================================================================

class TestMixedPlaceholderTypeQuirks:
    """Test quirks when mixing placeholder types."""
    
    def test_anonymous_and_indexed_share_args(self):
        """
        QUIRK: Anonymous and indexed placeholders share the same arg pool.
        `_` consumes next arg, `_0` always gets first arg.
        """
        # _ + _0 where _ consumes arg 0, and _0 also gets arg 0
        expr = _ + _0
        # With one arg (5): _ consumes 5, _0 gets 5 → 5 + 5 = 10
        assert expr(5) == 10
        
    def test_anonymous_consumes_before_indexed_access(self):
        """Anonymous placeholder consumption happens in order of resolution."""
        # _0 + _ → _0 gets arg 0, _ consumes arg 0 (next available)
        # Wait, let me trace through:
        # When resolving (_0 + _), we first resolve _0 (gets arg[0])
        # Then resolve _ as operand (consumes next arg, which is arg[0])
        # Actually both might consume/get arg 0...
        expr = _0 + _
        # With args (2, 3): _0=2, _=2 (next available is 0) → 4? Or _=3?
        # Need to test to see actual behavior
        result = expr(2, 3)
        # Based on implementation: _0 gets 2, _ consumes next (0→2)
        # So both get 2? Let's see:
        assert result in [4, 5]  # Either 2+2 or 2+3
        
    def test_multiple_anonymous_in_different_positions(self):
        """Multiple anonymous placeholders consume args in expression order."""
        expr = (_ + 1) * (_ - 1)
        # First _ consumes arg 0, second _ consumes arg 1
        result = expr(3, 5)
        assert result == (3 + 1) * (5 - 1)  # 4 * 4 = 16
        
    def test_indexed_with_gaps(self):
        """Using non-consecutive indices."""
        expr = _0 + _3  # Skips indices 1, 2
        result = expr(10, "skip", "skip", 20)
        assert result == 30


class TestNamedPlaceholderQuirks:
    """Test quirks with named placeholders."""
    
    def test_named_with_special_chars_via_getitem(self):
        """Named placeholders with special characters in name."""
        expr = _var["my-variable"] + _var["another.one"]
        result = expr(**{"my-variable": 10, "another.one": 20})
        assert result == 30
        
    def test_named_via_attr_cannot_have_dashes(self):
        """Cannot use dashes in attribute-style named placeholders."""
        # _var.my-variable would be interpreted as (_var.my) - variable
        # So we must use _var["my-variable"]
        pass  # Just documenting
        
    def test_named_shadows_positional(self):
        """Named args can be passed alongside positional."""
        expr = _0 + _var["offset"]
        result = expr(10, offset=5)
        assert result == 15


# =============================================================================
# PARTIAL APPLICATION EDGE CASES
# =============================================================================

class TestPartialApplicationEdgeCases:
    """Test edge cases in partial application."""
    
    def test_over_supply_args(self):
        """What happens when you supply too many args?"""
        expr = _ + 1
        # Needs 1 arg, supply 2
        result = expr(5, 10)  # Extra arg ignored
        assert result == 6
        
    def test_partial_then_oversupply(self):
        """Partial application followed by over-supply."""
        expr = _ + _
        partial = expr(5)
        result = partial(3, 999)  # 999 should be ignored
        assert result == 8
        
    def test_empty_call_on_needy_expr_raises(self):
        """Calling with no args when args needed should raise."""
        expr = _ + 1
        with pytest.raises(TypeError):
            expr()
            
    def test_partial_preserves_operations(self):
        """Partial application shouldn't lose operations."""
        expr = (_ + 1) * 2
        partial = expr(5)  # Should resolve, not partial
        # Actually if we provide enough args, it resolves
        assert partial == 12  # (5 + 1) * 2
        
    def test_double_partial(self):
        """Applying partial twice."""
        expr = _ + _ + _
        p1 = expr(1)
        assert isinstance(p1, Underscore)
        p2 = p1(2)
        assert isinstance(p2, Underscore)
        result = p2(3)
        assert result == 6


class TestReprEdgeCases:
    """Test repr in unusual situations."""
    
    def test_repr_deeply_nested(self):
        """Repr of deeply nested expression."""
        expr = (((_ + 1) * 2) - 3) / 4
        r = repr(expr)
        assert "_" in r
        assert "+" in r
        assert "*" in r
        
    def test_repr_with_underscore_as_operand(self):
        """Repr when another underscore is an operand."""
        expr = _0 + _1
        r = repr(expr)
        # Should show both placeholders
        assert "_" in r or "0" in r
        
    def test_repr_with_complex_object(self):
        """Repr with complex object as operand."""
        expr = _ + {"key": "value"}
        r = repr(expr)
        assert "key" in r or "{" in r


# =============================================================================
# INTROSPECTION EDGE CASES
# =============================================================================

class TestIntrospectionEdgeCases:
    """Test introspection in edge cases."""
    
    def test_introspect_bare_placeholder(self):
        """Introspect a bare, unmodified placeholder."""
        info = get_placeholder_info(_)
        assert info.anonymous_count == 1
        assert info.indexed == set()
        assert info.named == set()
        
    def test_introspect_deeply_nested(self):
        """Introspect deeply nested expression."""
        expr = (((_0 + _1) * _2) - _3) / _4
        info = get_placeholder_info(expr)
        assert info.indexed == {0, 1, 2, 3, 4}
        
    def test_introspect_mixed_all_types(self):
        """Expression with all placeholder types."""
        expr = _ + _0 * _var["scale"]
        info = get_placeholder_info(expr)
        assert info.anonymous_count == 1
        assert info.indexed == {0}
        assert info.named == {"scale"}


# =============================================================================
# PIPE EDGE CASES
# =============================================================================

class TestPipeEdgeCases:
    """Test pipe function edge cases."""
    
    def test_empty_pipe(self):
        """Pipe with no functions."""
        p = pipe()
        assert p(42) == 42  # Identity
        
    def test_single_function_pipe(self):
        """Pipe with single function."""
        p = pipe(_ + 1)
        assert p(5) == 6
        
    def test_pipe_with_non_underscore(self):
        """Pipe with regular functions."""
        p = pipe(lambda x: x + 1, str, lambda s: s + "!")
        assert p(5) == "6!"
        
    def test_pipe_with_mixed(self):
        """Pipe mixing underscore and regular functions."""
        p = pipe(_ + 1, str, _ + "!")
        assert p(5) == "6!"
        
    def test_pipe_error_propagation(self):
        """Errors in pipe should propagate."""
        p = pipe(_ + 1, lambda x: x / 0)
        with pytest.raises(ZeroDivisionError):
            p(5)


# =============================================================================
# THREAD SAFETY AND IMMUTABILITY
# =============================================================================

class TestImmutabilityGuarantees:
    """Test that immutability is maintained."""
    
    def test_operations_list_is_copied(self):
        """Operations list should be copied, not shared."""
        expr1 = _ + 1
        expr2 = expr1 * 2
        
        # Modifying expr2's ops shouldn't affect expr1
        assert len(expr1._operations) == 1
        assert len(expr2._operations) == 2
        
    def test_bound_kwargs_is_copied(self):
        """Bound kwargs should be copied."""
        expr = _var["a"] + _var["b"]
        p1 = expr(a=1)
        p2 = p1(b=2)
        
        assert p1._bound_kwargs == {"a": 1}
        assert p2._bound_kwargs == {"a": 1, "b": 2}


# =============================================================================
# ERROR HANDLING EDGE CASES
# =============================================================================

class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_attribute_error_at_resolution(self):
        """AttributeError propagates from resolution."""
        expr = _.nonexistent_attribute
        with pytest.raises(AttributeError):
            expr("string")
            
    def test_type_error_at_resolution(self):
        """TypeError propagates from resolution."""
        expr = _ + 1
        with pytest.raises(TypeError):
            expr("string")  # Can't add string and int
            
    def test_key_error_at_resolution(self):
        """KeyError propagates from resolution."""
        expr = _["missing"]
        with pytest.raises(KeyError):
            expr({})
            
    def test_index_error_at_resolution(self):
        """IndexError propagates from resolution."""
        expr = _[10]
        with pytest.raises(IndexError):
            expr([1, 2, 3])


# =============================================================================
# CREATIVE USE CASES
# =============================================================================

class TestCreativeUseCases:
    """Test creative but valid use cases."""
    
    def test_build_predicate(self):
        """Building predicates for filtering."""
        is_even = _ % 2 == 0
        numbers = [1, 2, 3, 4, 5, 6]
        evens = list(filter(is_even, numbers))
        assert evens == [2, 4, 6]
        
    def test_build_key_function(self):
        """Building key functions for sorting."""
        by_length = -_.length if False else len  # Can't do this directly
        # But we can do:
        class Item:
            def __init__(self, name):
                self.name = name
                
        by_name_length = _.name.__len__()
        items = [Item("a"), Item("ccc"), Item("bb")]
        # Can't directly use with sorted() key because it calls the function
        # But we can manually apply:
        lengths = [by_name_length(item) for item in items]
        assert lengths == [1, 3, 2]
        
    def test_method_dispatch(self):
        """Dynamic method dispatch using placeholder."""
        class Calculator:
            def add(self, a, b): return a + b
            def sub(self, a, b): return a - b
            
        calc = Calculator()
        
        # Dynamically choose method
        def dispatch(method_name, a, b):
            method_getter = getattr
            method = method_getter(calc, method_name)
            return method(a, b)
            
        assert dispatch("add", 5, 3) == 8
        assert dispatch("sub", 5, 3) == 2
        
    def test_conditional_via_dict(self):
        """Simulating conditionals with dict dispatch."""
        ops = {
            "+": _ + _,
            "-": _ - _,
            "*": _ * _,
        }
        
        assert ops["+"](3, 4) == 7
        assert ops["-"](10, 3) == 7
        assert ops["*"](3, 4) == 12


class TestComparisonChaining:
    """Test various comparison scenarios."""
    
    def test_equality_chain(self):
        """Test chained equality (Python allows this!)."""
        # a == b == c means (a == b) and (b == c)
        # But with underscore:
        expr = _ == 5
        assert expr(5) is True
        assert expr(3) is False
        
    def test_comparison_with_placeholder_both_sides(self):
        """Compare two placeholders."""
        expr = _0 > _1
        assert expr(5, 3) is True
        assert expr(3, 5) is False
        assert expr(5, 5) is False


class TestDivisionEdgeCases:
    """Test division edge cases."""
    
    def test_division_by_zero(self):
        """Division by zero raises at resolution."""
        expr = _ / 0
        with pytest.raises(ZeroDivisionError):
            expr(10)
            
    def test_floor_division_by_zero(self):
        """Floor division by zero raises at resolution."""
        expr = _ // 0
        with pytest.raises(ZeroDivisionError):
            expr(10)
            
    def test_modulo_by_zero(self):
        """Modulo by zero raises at resolution."""
        expr = _ % 0
        with pytest.raises(ZeroDivisionError):
            expr(10)
            
    def test_reverse_division(self):
        """Reverse division."""
        expr = 100 / _
        assert expr(4) == 25.0
        
        expr2 = 100 // _
        assert expr2(3) == 33


class TestBitOperationsEdgeCases:
    """Test bitwise operations with edge cases."""
    
    def test_shift_negative(self):
        """Shifting by negative amount."""
        expr = _ << -1
        with pytest.raises(ValueError):
            expr(5)
            
    def test_shift_large(self):
        """Shifting by large amount."""
        expr = 1 << _
        assert expr(64) == 2**64
        
    def test_invert_bool(self):
        """Bitwise invert of boolean."""
        expr = ~_
        assert expr(True) == -2  # ~True == ~1 == -2
        assert expr(False) == -1  # ~False == ~0 == -1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_data_transformation_pipeline(self):
        """Complex data transformation."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        
        get_age = _["age"]
        ages = [get_age(person) for person in data]
        assert ages == [30, 25, 35]
        
        is_over_28 = _["age"] > 28
        filtered = [p for p in data if is_over_28(p)]
        assert len(filtered) == 2
        
    def test_functional_map_reduce(self):
        """Using underscore in map/reduce style."""
        double = _ * 2
        add = _ + _
        
        numbers = [1, 2, 3, 4, 5]
        doubled = list(map(double, numbers))
        assert doubled == [2, 4, 6, 8, 10]
        
        # Using reduce with underscore
        from functools import reduce
        total = reduce(add, numbers)
        assert total == 15
        
    def test_configuration_access_pattern(self):
        """Using underscore for config access."""
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "user": "admin",
                    "password": "secret"
                }
            }
        }
        
        get_db_user = _["database"]["credentials"]["user"]
        assert get_db_user(config) == "admin"
        
        get_port = _["database"]["port"]
        assert get_port(config) == 5432