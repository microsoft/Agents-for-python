"""
Unit tests for the quantifier module.

This module tests:
- Quantifier protocol
- for_all function
- for_any function
- for_none function
- for_one function
- for_n factory function
"""

import pytest
from microsoft_agents.testing.check.quantifier import (
    Quantifier,
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)


# =============================================================================
# for_all Tests
# =============================================================================

class TestForAll:
    """Test the for_all quantifier."""
    
    def test_all_true(self):
        assert for_all([True, True, True]) is True
    
    def test_all_false(self):
        assert for_all([False, False, False]) is False
    
    def test_mixed_values(self):
        assert for_all([True, False, True]) is False
    
    def test_single_true(self):
        assert for_all([True]) is True
    
    def test_single_false(self):
        assert for_all([False]) is False
    
    def test_empty_list(self):
        # all() on empty iterable returns True
        assert for_all([]) is True
    
    def test_one_false_among_many(self):
        assert for_all([True, True, True, False, True]) is False


# =============================================================================
# for_any Tests
# =============================================================================

class TestForAny:
    """Test the for_any quantifier."""
    
    def test_all_true(self):
        assert for_any([True, True, True]) is True
    
    def test_all_false(self):
        assert for_any([False, False, False]) is False
    
    def test_mixed_values(self):
        assert for_any([True, False, True]) is True
    
    def test_single_true(self):
        assert for_any([True]) is True
    
    def test_single_false(self):
        assert for_any([False]) is False
    
    def test_empty_list(self):
        # any() on empty iterable returns False
        assert for_any([]) is False
    
    def test_one_true_among_many(self):
        assert for_any([False, False, False, True, False]) is True


# =============================================================================
# for_none Tests
# =============================================================================

class TestForNone:
    """Test the for_none quantifier."""
    
    def test_all_false(self):
        assert for_none([False, False, False]) is True
    
    def test_all_true(self):
        assert for_none([True, True, True]) is False
    
    def test_mixed_values(self):
        assert for_none([True, False, True]) is False
    
    def test_single_true(self):
        assert for_none([True]) is False
    
    def test_single_false(self):
        assert for_none([False]) is True
    
    def test_empty_list(self):
        # all(not x for x in []) returns True
        assert for_none([]) is True
    
    def test_one_true_among_many(self):
        assert for_none([False, False, True, False]) is False


# =============================================================================
# for_one Tests
# =============================================================================

class TestForOne:
    """Test the for_one quantifier."""
    
    def test_exactly_one_true(self):
        assert for_one([False, True, False]) is True
    
    def test_no_true(self):
        assert for_one([False, False, False]) is False
    
    def test_multiple_true(self):
        assert for_one([True, True, False]) is False
    
    def test_all_true(self):
        assert for_one([True, True, True]) is False
    
    def test_single_true(self):
        assert for_one([True]) is True
    
    def test_single_false(self):
        assert for_one([False]) is False
    
    def test_empty_list(self):
        assert for_one([]) is False
    
    def test_first_is_only_true(self):
        assert for_one([True, False, False, False]) is True
    
    def test_last_is_only_true(self):
        assert for_one([False, False, False, True]) is True


# =============================================================================
# for_n Factory Tests
# =============================================================================

class TestForN:
    """Test the for_n factory function."""
    
    def test_for_zero(self):
        quantifier = for_n(0)
        assert quantifier([False, False, False]) is True
        assert quantifier([True, False, False]) is False
        assert quantifier([]) is True
    
    def test_for_one_equivalent(self):
        quantifier = for_n(1)
        assert quantifier([True]) is True
        assert quantifier([True, True]) is False
        assert quantifier([False]) is False
    
    def test_for_two(self):
        quantifier = for_n(2)
        assert quantifier([True, True]) is True
        assert quantifier([True, True, True]) is False
        assert quantifier([True, False, True]) is True
        assert quantifier([True]) is False
    
    def test_for_three(self):
        quantifier = for_n(3)
        assert quantifier([True, True, True]) is True
        assert quantifier([True, True]) is False
        assert quantifier([True, True, True, True]) is False
    
    def test_for_large_n(self):
        quantifier = for_n(5)
        assert quantifier([True] * 5) is True
        assert quantifier([True] * 4 + [False]) is False
        assert quantifier([True] * 6) is False
    
    def test_returns_callable(self):
        quantifier = for_n(2)
        assert callable(quantifier)
    
    def test_n_zero_with_all_false(self):
        quantifier = for_n(0)
        assert quantifier([False, False, False, False]) is True
    
    def test_n_equals_list_length(self):
        quantifier = for_n(4)
        assert quantifier([True, True, True, True]) is True
        assert quantifier([True, True, True, False]) is False


# =============================================================================
# Quantifier Protocol Tests
# =============================================================================

class TestQuantifierProtocol:
    """Test that quantifiers conform to the Quantifier protocol."""
    
    def test_for_all_is_callable(self):
        assert callable(for_all)
    
    def test_for_any_is_callable(self):
        assert callable(for_any)
    
    def test_for_none_is_callable(self):
        assert callable(for_none)
    
    def test_for_one_is_callable(self):
        assert callable(for_one)
    
    def test_for_n_returns_callable(self):
        assert callable(for_n(2))
    
    def test_all_return_bool(self):
        test_list = [True, False, True]
        assert isinstance(for_all(test_list), bool)
        assert isinstance(for_any(test_list), bool)
        assert isinstance(for_none(test_list), bool)
        assert isinstance(for_one(test_list), bool)
        assert isinstance(for_n(1)(test_list), bool)


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestQuantifierEdgeCases:
    """Test edge cases for quantifiers."""
    
    def test_large_list_all_true(self):
        large_list = [True] * 1000
        assert for_all(large_list) is True
        assert for_any(large_list) is True
        assert for_none(large_list) is False
    
    def test_large_list_all_false(self):
        large_list = [False] * 1000
        assert for_all(large_list) is False
        assert for_any(large_list) is False
        assert for_none(large_list) is True
    
    def test_large_list_mixed(self):
        large_list = [True] * 500 + [False] * 500
        assert for_all(large_list) is False
        assert for_any(large_list) is True
        assert for_none(large_list) is False
        assert for_n(500)(large_list) is True
    
    def test_alternating_values(self):
        alternating = [True, False] * 50
        assert for_all(alternating) is False
        assert for_any(alternating) is True
        assert for_none(alternating) is False
        assert for_n(50)(alternating) is True
