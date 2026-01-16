import pytest

from microsoft_agents.testing.check.quantifier import (
    for_all,
    for_any,
    for_none,
    for_exactly,
    for_one,
)


class TestForAll:
    """Test for_all quantifier."""

    def test_all_items_match(self):
        """Test when all items satisfy the predicate."""
        items = [2, 4, 6, 8]
        result = for_all(items, lambda x: x % 2 == 0)
        assert result is True

    def test_some_items_do_not_match(self):
        """Test when some items do not satisfy the predicate."""
        items = [2, 4, 5, 8]
        result = for_all(items, lambda x: x % 2 == 0)
        assert result is False

    def test_no_items_match(self):
        """Test when no items satisfy the predicate."""
        items = [1, 3, 5, 7]
        result = for_all(items, lambda x: x % 2 == 0)
        assert result is False

    def test_empty_iterable(self):
        """Test with empty iterable - should return True (vacuous truth)."""
        items = []
        result = for_all(items, lambda x: x > 0)
        assert result is True

    def test_single_item_matches(self):
        """Test with single item that matches."""
        items = [5]
        result = for_all(items, lambda x: x > 0)
        assert result is True

    def test_single_item_does_not_match(self):
        """Test with single item that does not match."""
        items = [-1]
        result = for_all(items, lambda x: x > 0)
        assert result is False

    def test_with_strings(self):
        """Test with string items."""
        items = ["apple", "apricot", "avocado"]
        result = for_all(items, lambda x: x.startswith("a"))
        assert result is True

    def test_with_generator(self):
        """Test with generator instead of list."""
        items = (x for x in range(1, 5))
        result = for_all(items, lambda x: x > 0)
        assert result is True


class TestForAny:
    """Test for_any quantifier."""

    def test_all_items_match(self):
        """Test when all items satisfy the predicate."""
        items = [2, 4, 6, 8]
        result = for_any(items, lambda x: x % 2 == 0)
        assert result is True

    def test_some_items_match(self):
        """Test when some items satisfy the predicate."""
        items = [1, 2, 3, 4]
        result = for_any(items, lambda x: x % 2 == 0)
        assert result is True

    def test_no_items_match(self):
        """Test when no items satisfy the predicate."""
        items = [1, 3, 5, 7]
        result = for_any(items, lambda x: x % 2 == 0)
        assert result is False

    def test_empty_iterable(self):
        """Test with empty iterable - should return False."""
        items = []
        result = for_any(items, lambda x: x > 0)
        assert result is False

    def test_single_item_matches(self):
        """Test with single item that matches."""
        items = [5]
        result = for_any(items, lambda x: x > 0)
        assert result is True

    def test_single_item_does_not_match(self):
        """Test with single item that does not match."""
        items = [-1]
        result = for_any(items, lambda x: x > 0)
        assert result is False

    def test_first_item_matches(self):
        """Test when first item matches (short-circuit behavior)."""
        items = [2, 1, 3, 5]
        result = for_any(items, lambda x: x % 2 == 0)
        assert result is True

    def test_last_item_matches(self):
        """Test when only last item matches."""
        items = [1, 3, 5, 6]
        result = for_any(items, lambda x: x % 2 == 0)
        assert result is True


class TestForNone:
    """Test for_none quantifier."""

    def test_no_items_match(self):
        """Test when no items satisfy the predicate."""
        items = [1, 3, 5, 7]
        result = for_none(items, lambda x: x % 2 == 0)
        assert result is True

    def test_some_items_match(self):
        """Test when some items satisfy the predicate."""
        items = [1, 2, 3, 4]
        result = for_none(items, lambda x: x % 2 == 0)
        assert result is False

    def test_all_items_match(self):
        """Test when all items satisfy the predicate."""
        items = [2, 4, 6, 8]
        result = for_none(items, lambda x: x % 2 == 0)
        assert result is False

    def test_empty_iterable(self):
        """Test with empty iterable - should return True."""
        items = []
        result = for_none(items, lambda x: x > 0)
        assert result is True

    def test_single_item_matches(self):
        """Test with single item that matches predicate."""
        items = [2]
        result = for_none(items, lambda x: x % 2 == 0)
        assert result is False

    def test_single_item_does_not_match(self):
        """Test with single item that does not match predicate."""
        items = [1]
        result = for_none(items, lambda x: x % 2 == 0)
        assert result is True

    def test_with_strings(self):
        """Test with string items."""
        items = ["banana", "cherry", "date"]
        result = for_none(items, lambda x: x.startswith("a"))
        assert result is True


class TestForExactly:
    """Test for_exactly quantifier factory."""

    def test_exactly_zero_matches(self):
        """Test for_exactly(0) when no items match."""
        items = [1, 3, 5, 7]
        quantifier = for_exactly(0)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is True

    def test_exactly_zero_but_some_match(self):
        """Test for_exactly(0) when some items match."""
        items = [1, 2, 3, 4]
        quantifier = for_exactly(0)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is False

    def test_exactly_one_match(self):
        """Test for_exactly(1) when exactly one item matches."""
        items = [1, 2, 3, 5]
        quantifier = for_exactly(1)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is True

    def test_exactly_one_but_two_match(self):
        """Test for_exactly(1) when two items match."""
        items = [1, 2, 3, 4]
        quantifier = for_exactly(1)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is False

    def test_exactly_two_matches(self):
        """Test for_exactly(2) when exactly two items match."""
        items = [1, 2, 3, 4]
        quantifier = for_exactly(2)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is True

    def test_exactly_two_but_three_match(self):
        """Test for_exactly(2) when three items match."""
        items = [2, 4, 6, 7]
        quantifier = for_exactly(2)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is False

    def test_exactly_n_matches_all(self):
        """Test for_exactly(n) when all n items match."""
        items = [2, 4, 6, 8]
        quantifier = for_exactly(4)
        result = quantifier(items, lambda x: x % 2 == 0)
        assert result is True

    def test_empty_iterable_exactly_zero(self):
        """Test for_exactly(0) with empty iterable."""
        items = []
        quantifier = for_exactly(0)
        result = quantifier(items, lambda x: x > 0)
        assert result is True

    def test_empty_iterable_exactly_one(self):
        """Test for_exactly(1) with empty iterable."""
        items = []
        quantifier = for_exactly(1)
        result = quantifier(items, lambda x: x > 0)
        assert result is False

    def test_for_exactly_is_reusable(self):
        """Test that the returned quantifier can be reused."""
        quantifier = for_exactly(2)
        
        items1 = [1, 2, 3, 4]
        items2 = [2, 4, 6]
        
        assert quantifier(items1, lambda x: x % 2 == 0) is True
        assert quantifier(items2, lambda x: x % 2 == 0) is False


class TestForOne:
    """Test for_one quantifier."""

    def test_exactly_one_match(self):
        """Test when exactly one item matches."""
        items = [1, 2, 3, 5]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is True

    def test_no_items_match(self):
        """Test when no items match."""
        items = [1, 3, 5, 7]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is False

    def test_multiple_items_match(self):
        """Test when multiple items match."""
        items = [2, 4, 6, 8]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is False

    def test_empty_iterable(self):
        """Test with empty iterable."""
        items = []
        result = for_one(items, lambda x: x > 0)
        assert result is False

    def test_single_item_matches(self):
        """Test with single item that matches."""
        items = [2]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is True

    def test_single_item_does_not_match(self):
        """Test with single item that does not match."""
        items = [1]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is False

    def test_first_item_is_the_one(self):
        """Test when first item is the only match."""
        items = [2, 1, 3, 5]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is True

    def test_last_item_is_the_one(self):
        """Test when last item is the only match."""
        items = [1, 3, 5, 6]
        result = for_one(items, lambda x: x % 2 == 0)
        assert result is True


class TestQuantifiersWithComplexPredicates:
    """Test quantifiers with more complex predicates and data types."""

    def test_for_all_with_dict_items(self):
        """Test for_all with dictionary items."""
        items = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 35},
        ]
        result = for_all(items, lambda x: x["age"] >= 25)
        assert result is True

    def test_for_any_with_dict_items(self):
        """Test for_any with dictionary items."""
        items = [
            {"name": "Alice", "active": False},
            {"name": "Bob", "active": True},
            {"name": "Charlie", "active": False},
        ]
        result = for_any(items, lambda x: x["active"])
        assert result is True

    def test_for_none_with_dict_items(self):
        """Test for_none with dictionary items."""
        items = [
            {"name": "Alice", "deleted": False},
            {"name": "Bob", "deleted": False},
        ]
        result = for_none(items, lambda x: x["deleted"])
        assert result is True

    def test_for_exactly_with_dict_items(self):
        """Test for_exactly with dictionary items."""
        items = [
            {"name": "Alice", "role": "admin"},
            {"name": "Bob", "role": "user"},
            {"name": "Charlie", "role": "admin"},
        ]
        quantifier = for_exactly(2)
        result = quantifier(items, lambda x: x["role"] == "admin")
        assert result is True

    def test_for_one_with_dict_items(self):
        """Test for_one with dictionary items."""
        items = [
            {"name": "Alice", "is_owner": False},
            {"name": "Bob", "is_owner": True},
            {"name": "Charlie", "is_owner": False},
        ]
        result = for_one(items, lambda x: x["is_owner"])
        assert result is True