# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Comprehensive tests for the Check class.
Tests cover initialization, selectors, quantifier-based assertions,
terminal operations, and integration scenarios.
"""

import pytest
from pydantic import BaseModel
from typing import Any

from microsoft_agents.testing.check import Check
from microsoft_agents.testing.check.quantifier import (
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)


# Test fixtures - Pydantic models for testing
class Message(BaseModel):
    type: str
    text: str | None = None
    attachments: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Response(BaseModel):
    status: str
    code: int
    data: dict[str, Any] | None = None


# =============================================================================
# TestCheckInit - Initialization tests
# =============================================================================

class TestCheckInit:
    """Test Check initialization."""

    def test_init_with_empty_list(self):
        """Check initializes correctly with an empty list."""
        check = Check([])
        assert check._items == []

    def test_init_with_dict_items(self):
        """Check initializes correctly with dict items."""
        items = [{"type": "message", "text": "hello"}]
        check = Check(items)
        assert check._items == items

    def test_init_with_pydantic_models(self):
        """Check initializes correctly with Pydantic models."""
        items = [Message(type="message", text="hello")]
        check = Check(items)
        assert len(check._items) == 1
        assert check._items[0].type == "message"

    def test_init_with_mixed_items(self):
        """Check initializes with mixed dict and Pydantic models."""
        items = [
            {"type": "dict_item"},
            Message(type="pydantic_item", text="hello"),
        ]
        check = Check(items)
        assert len(check._items) == 2

    def test_init_converts_iterable_to_list(self):
        """Check converts any iterable to a list."""
        items = iter([{"type": "message"}, {"type": "typing"}])
        check = Check(items)
        assert isinstance(check._items, list)
        assert len(check._items) == 2

    def test_init_with_generator(self):
        """Check works with generator expressions."""
        gen = ({"id": i} for i in range(3))
        check = Check(gen)
        assert len(check._items) == 3
        assert check._items[0]["id"] == 0

    def test_init_creates_engine(self):
        """Check creates a CheckEngine on initialization."""
        check = Check([{"id": 1}])
        assert check._engine is not None


# =============================================================================
# TestCheckWhere - Filtering tests
# =============================================================================

class TestCheckWhere:
    """Test Check.where() filtering."""

    def test_where_filters_by_single_field(self):
        """where() filters items by a single field match."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        check = Check(items).where(type="message")
        assert len(check._items) == 2
        assert all(item["type"] == "message" for item in check._items)

    def test_where_filters_by_multiple_fields(self):
        """where() filters items by multiple field matches."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message", text="hello")
        assert len(check._items) == 1
        assert check._items[0]["text"] == "hello"

    def test_where_with_dict_filter(self):
        """where() accepts a dict as filter criteria."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
        ]
        check = Check(items).where({"type": "message"})
        assert len(check._items) == 1
        assert check._items[0]["type"] == "message"

    def test_where_with_combined_dict_and_kwargs(self):
        """where() combines dict filter with kwargs."""
        items = [
            {"type": "message", "text": "hello", "urgent": True},
            {"type": "message", "text": "world", "urgent": False},
        ]
        check = Check(items).where({"type": "message"}, urgent=True)
        assert len(check._items) == 1
        assert check._items[0]["text"] == "hello"

    def test_where_returns_empty_when_no_match(self):
        """where() returns empty Check when no items match."""
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="unknown")
        assert len(check._items) == 0

    def test_where_is_chainable(self):
        """where() can be chained multiple times."""
        items = [
            {"type": "message", "text": "hello", "urgent": True},
            {"type": "message", "text": "world", "urgent": False},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message").where(urgent=True)
        assert len(check._items) == 1
        assert check._items[0]["text"] == "hello"

    def test_where_with_pydantic_models(self):
        """where() works with Pydantic models."""
        items = [
            Message(type="message", text="hello"),
            Message(type="typing"),
            Message(type="message", text="world"),
        ]
        check = Check(items).where(type="message")
        assert len(check._items) == 2

    def test_where_with_callable_filter(self):
        """where() accepts a callable filter."""
        items = [
            {"type": "message", "count": 5},
            {"type": "message", "count": 10},
            {"type": "message", "count": 3},
        ]
        check = Check(items).where(count=lambda actual: actual > 4)
        assert len(check._items) == 2

    def test_where_with_nested_field(self):
        """where() can filter on nested dict fields."""
        items = [
            {"type": "message", "meta": {"priority": "high"}},
            {"type": "message", "meta": {"priority": "low"}},
        ]
        check = Check(items).where(meta={"priority": "high"})
        assert len(check._items) == 1


# =============================================================================
# TestCheckWhereNot - Exclusion filtering tests
# =============================================================================

class TestCheckWhereNot:
    """Test Check.where_not() exclusion filtering."""

    def test_where_not_excludes_matching_items(self):
        """where_not() excludes items that match criteria."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        check = Check(items).where_not(type="message")
        assert len(check._items) == 1
        assert check._items[0]["type"] == "typing"

    def test_where_not_with_multiple_fields(self):
        """where_not() excludes items matching all fields."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="message", text="hello")
        assert len(check._items) == 2

    def test_where_not_returns_all_when_no_match(self):
        """where_not() returns all items when none match exclusion."""
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="unknown")
        assert len(check._items) == 2

    def test_where_not_is_chainable(self):
        """where_not() can be chained."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="typing").where_not(text="hello")
        assert len(check._items) == 1
        assert check._items[0]["text"] == "world"

    def test_where_not_combined_with_where(self):
        """where_not() can be combined with where()."""
        items = [
            {"type": "message", "status": "sent"},
            {"type": "message", "status": "pending"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message").where_not(status="pending")
        assert len(check._items) == 1
        assert check._items[0]["status"] == "sent"


# =============================================================================
# TestCheckMerge - Merging tests
# =============================================================================

class TestCheckMerge:
    """Test Check.merge() combining checks."""

    def test_merge_combines_items(self):
        """merge() combines items from two Check instances."""
        items1 = [{"type": "message", "text": "hello"}]
        items2 = [{"type": "typing"}]
        check1 = Check(items1)
        check2 = Check(items2)
        merged = check1.merge(check2)
        assert len(merged._items) == 2

    def test_merge_preserves_order(self):
        """merge() preserves order: first Check's items, then second's."""
        items1 = [{"id": 1}, {"id": 2}]
        items2 = [{"id": 3}, {"id": 4}]
        merged = Check(items1).merge(Check(items2))
        assert [item["id"] for item in merged._items] == [1, 2, 3, 4]

    def test_merge_empty_checks(self):
        """merge() works with empty Check instances."""
        check1 = Check([])
        check2 = Check([])
        merged = check1.merge(check2)
        assert len(merged._items) == 0

    def test_merge_with_one_empty(self):
        """merge() works when one Check is empty."""
        items = [{"id": 1}]
        merged = Check(items).merge(Check([]))
        assert len(merged._items) == 1
        
        merged2 = Check([]).merge(Check(items))
        assert len(merged2._items) == 1

    def test_merge_is_chainable(self):
        """merge() can be chained multiple times."""
        c1 = Check([{"id": 1}])
        c2 = Check([{"id": 2}])
        c3 = Check([{"id": 3}])
        merged = c1.merge(c2).merge(c3)
        assert len(merged._items) == 3


# =============================================================================
# TestCheckPositionalSelectors - first(), last(), at(), cap()
# =============================================================================

class TestCheckPositionalSelectors:
    """Test Check positional selectors: first(), last(), at(), cap()."""

    def test_first_returns_first_item(self):
        """first() selects only the first item."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).first()
        assert len(check._items) == 1
        assert check._items[0]["id"] == 1

    def test_first_on_empty_list(self):
        """first() on empty list returns empty Check."""
        check = Check([]).first()
        assert len(check._items) == 0

    def test_first_on_single_item(self):
        """first() on single item works correctly."""
        check = Check([{"id": 1}]).first()
        assert len(check._items) == 1

    def test_last_returns_last_item(self):
        """last() selects only the last item."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).last()
        assert len(check._items) == 1
        assert check._items[0]["id"] == 3

    def test_last_on_empty_list(self):
        """last() on empty list returns empty Check."""
        check = Check([]).last()
        assert len(check._items) == 0

    def test_last_on_single_item(self):
        """last() on single item works correctly."""
        check = Check([{"id": 1}]).last()
        assert len(check._items) == 1

    def test_at_returns_nth_item(self):
        """at(n) selects the item at index n."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).at(1)
        assert len(check._items) == 1
        assert check._items[0]["id"] == 2

    def test_at_first_index(self):
        """at(0) selects the first item."""
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).at(0)
        assert check._items[0]["id"] == 1

    def test_at_last_index(self):
        """at() with last index selects last item."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).at(2)
        assert len(check._items) == 1
        assert check._items[0]["id"] == 3

    def test_at_out_of_bounds(self):
        """at() with out of bounds index returns empty Check."""
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).at(5)
        assert len(check._items) == 0

    def test_at_negative_index(self):
        """at() with negative index behavior."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).at(-1)
        # Slicing [-1:-1+1] = [-1:0] which is empty
        # This tests current behavior
        assert len(check._items) == 0

    def test_cap_limits_items(self):
        """cap(n) limits selection to first n items."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        check = Check(items).cap(2)
        assert len(check._items) == 2
        assert check._items[0]["id"] == 1
        assert check._items[1]["id"] == 2

    def test_cap_with_larger_n_than_items(self):
        """cap(n) with n > len(items) returns all items."""
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).cap(10)
        assert len(check._items) == 2

    def test_cap_zero(self):
        """cap(0) returns empty Check."""
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).cap(0)
        assert len(check._items) == 0

    def test_selectors_are_chainable(self):
        """Positional selectors can be chained with where()."""
        items = [
            {"type": "message", "id": 1},
            {"type": "typing", "id": 2},
            {"type": "message", "id": 3},
        ]
        check = Check(items).where(type="message").first()
        assert len(check._items) == 1
        assert check._items[0]["id"] == 1


# =============================================================================
# TestCheckThat - Assertion tests
# =============================================================================

class TestCheckThat:
    """Test Check.that() and related assertion methods."""

    def test_that_passes_when_all_match(self):
        """that() passes when all items match criteria."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "hello"},
        ]
        # Should not raise
        Check(items).that(text="hello")

    def test_that_fails_when_not_all_match(self):
        """that() fails when not all items match."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that(text="hello")

    def test_that_with_multiple_criteria(self):
        """that() can check multiple criteria at once."""
        items = [{"type": "message", "text": "hello", "urgent": True}]
        Check(items).that(type="message", text="hello", urgent=True)

    def test_that_with_dict_assertion(self):
        """that() accepts a dict as assertion criteria."""
        items = [{"type": "message", "text": "hello"}]
        Check(items).that({"type": "message", "text": "hello"})

    def test_that_with_callable_assertion(self):
        """that() accepts callable for field validation."""
        items = [{"type": "message", "count": 5}]
        Check(items).that(count=lambda actual: actual > 3)

    def test_that_fails_with_callable_returning_false(self):
        """that() fails when callable returns False."""
        items = [{"count": 5}]
        with pytest.raises(AssertionError):
            Check(items).that(count=lambda actual: actual > 10)

    def test_that_after_where_filter(self):
        """that() works after where() filtering."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        Check(items).where(type="message").that(type="message")

    def test_that_on_empty_raises(self):
        """that() on empty list with for_all should handle edge case."""
        # for_all on empty list returns True (vacuous truth)
        # This should not raise
        Check([]).that(type="message")


# =============================================================================
# TestCheckThatForAny - that_for_any() tests
# =============================================================================

class TestCheckThatForAny:
    """Test Check.that_for_any() assertions."""

    def test_that_for_any_passes_when_any_match(self):
        """that_for_any() passes when at least one item matches."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).that_for_any(text="hello")

    def test_that_for_any_fails_when_none_match(self):
        """that_for_any() fails when no items match."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_any(text="unknown")

    def test_that_for_any_with_single_matching_item(self):
        """that_for_any() passes with exactly one matching item."""
        items = [{"text": "hello"}, {"text": "world"}, {"text": "foo"}]
        Check(items).that_for_any(text="world")

    def test_that_for_any_on_empty_fails(self):
        """that_for_any() on empty list fails (no item can match)."""
        with pytest.raises(AssertionError):
            Check([]).that_for_any(type="message")


# =============================================================================
# TestCheckThatForAll - that_for_all() tests
# =============================================================================

class TestCheckThatForAll:
    """Test Check.that_for_all() assertions."""

    def test_that_for_all_passes_when_all_match(self):
        """that_for_all() passes when all items match."""
        items = [
            {"type": "message"},
            {"type": "message"},
        ]
        Check(items).that_for_all(type="message")

    def test_that_for_all_fails_when_one_doesnt_match(self):
        """that_for_all() fails when any item doesn't match."""
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_all(type="message")

    def test_that_for_all_on_empty_passes(self):
        """that_for_all() on empty list passes (vacuous truth)."""
        Check([]).that_for_all(type="message")


# =============================================================================
# TestCheckThatForNone - that_for_none() tests
# =============================================================================

class TestCheckThatForNone:
    """Test Check.that_for_none() assertions."""

    def test_that_for_none_passes_when_none_match(self):
        """that_for_none() passes when no items match criteria."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).that_for_none(text="unknown")

    def test_that_for_none_fails_when_any_match(self):
        """that_for_none() fails when any item matches."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_none(text="hello")

    def test_that_for_none_on_empty_passes(self):
        """that_for_none() on empty list passes."""
        Check([]).that_for_none(type="message")


# =============================================================================
# TestCheckThatForOne - that_for_one() tests
# =============================================================================

class TestCheckThatForOne:
    """Test Check.that_for_one() assertions."""

    def test_that_for_one_passes_when_exactly_one_matches(self):
        """that_for_one() passes when exactly one item matches."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).that_for_one(text="hello")

    def test_that_for_one_fails_when_multiple_match(self):
        """that_for_one() fails when multiple items match."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "hello"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_one(text="hello")

    def test_that_for_one_fails_when_none_match(self):
        """that_for_one() fails when no items match."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_one(text="unknown")

    def test_that_for_one_on_empty_fails(self):
        """that_for_one() on empty list fails."""
        with pytest.raises(AssertionError):
            Check([]).that_for_one(type="message")


# =============================================================================
# TestCheckThatForExactly - that_for_exactly() tests
# =============================================================================

class TestCheckThatForExactly:
    """Test Check.that_for_exactly() assertions."""

    def test_that_for_exactly_passes_with_correct_count(self):
        """that_for_exactly(n) passes when exactly n items match."""
        items = [
            {"type": "message"},
            {"type": "message"},
            {"type": "typing"},
        ]
        Check(items).that_for_exactly(2, type="message")

    def test_that_for_exactly_fails_with_fewer(self):
        """that_for_exactly(n) fails when fewer than n items match."""
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_exactly(2, type="message")

    def test_that_for_exactly_fails_with_more(self):
        """that_for_exactly(n) fails when more than n items match."""
        items = [
            {"type": "message"},
            {"type": "message"},
            {"type": "message"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that_for_exactly(2, type="message")

    def test_that_for_exactly_zero(self):
        """that_for_exactly(0) passes when no items match."""
        items = [{"type": "typing"}, {"type": "typing"}]
        Check(items).that_for_exactly(0, type="message")

    def test_that_for_exactly_on_empty(self):
        """that_for_exactly(0) on empty list passes."""
        Check([]).that_for_exactly(0, type="message")

    def test_that_for_exactly_n_on_empty_fails_for_n_gt_0(self):
        """that_for_exactly(n>0) on empty list fails."""
        with pytest.raises(AssertionError):
            Check([]).that_for_exactly(1, type="message")


# =============================================================================
# TestCheckTerminalOperations - get(), get_one(), count(), exists()
# =============================================================================

class TestCheckTerminalOperations:
    """Test Check terminal operations: get(), get_one(), count(), exists()."""

    def test_get_returns_items_list(self):
        """get() returns the items as a list."""
        items = [{"id": 1}, {"id": 2}]
        result = Check(items).get()
        assert result == items
        assert isinstance(result, list)

    def test_get_returns_filtered_items(self):
        """get() returns items after filtering."""
        items = [{"type": "message"}, {"type": "typing"}]
        result = Check(items).where(type="message").get()
        assert len(result) == 1
        assert result[0]["type"] == "message"

    def test_get_returns_empty_list(self):
        """get() returns empty list when no items."""
        result = Check([]).get()
        assert result == []

    def test_get_one_returns_single_item(self):
        """get_one() returns the single item."""
        items = [{"id": 1}]
        result = Check(items).get_one()
        assert result == {"id": 1}

    def test_get_one_raises_when_empty(self):
        """get_one() raises ValueError when empty."""
        with pytest.raises(ValueError, match="Expected exactly one item"):
            Check([]).get_one()

    def test_get_one_raises_when_multiple(self):
        """get_one() raises ValueError when multiple items."""
        items = [{"id": 1}, {"id": 2}]
        with pytest.raises(ValueError, match="Expected exactly one item"):
            Check(items).get_one()

    def test_get_one_after_first(self):
        """get_one() works after first()."""
        items = [{"id": 1}, {"id": 2}]
        result = Check(items).first().get_one()
        assert result["id"] == 1

    def test_count_returns_number_of_items(self):
        """count() returns the number of items."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        assert Check(items).count() == 3

    def test_count_returns_zero_for_empty(self):
        """count() returns 0 for empty list."""
        assert Check([]).count() == 0

    def test_count_after_filter(self):
        """count() returns count after filtering."""
        items = [{"type": "message"}, {"type": "typing"}, {"type": "message"}]
        assert Check(items).where(type="message").count() == 2

    def test_exists_returns_true_when_items_present(self):
        """exists() returns True when items are present."""
        items = [{"id": 1}]
        assert Check(items).exists() is True

    def test_exists_returns_false_when_empty(self):
        """exists() returns False when no items."""
        assert Check([]).exists() is False

    def test_exists_after_filter(self):
        """exists() works correctly after filtering."""
        items = [{"type": "message"}, {"type": "typing"}]
        assert Check(items).where(type="message").exists() is True
        assert Check(items).where(type="unknown").exists() is False


# =============================================================================
# TestCheckBoolList - _bool_list() tests
# =============================================================================

class TestCheckBoolList:
    """Test Check._bool_list() method."""

    def test_bool_list_returns_all_true(self):
        """_bool_list() returns a list of True for each item."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items)
        result = check._bool_list()
        assert result == [True, True, True]

    def test_bool_list_empty(self):
        """_bool_list() returns empty list for empty Check."""
        check = Check([])
        result = check._bool_list()
        assert result == []


# =============================================================================
# TestCheckChildInheritance - _child() method tests
# =============================================================================

class TestCheckChildInheritance:
    """Test that child Check instances properly inherit engine and state."""

    def test_child_inherits_engine(self):
        """Child Check inherits parent's engine."""
        check = Check([{"id": 1}])
        child = check.first()
        assert child._engine is check._engine

    def test_child_has_correct_items(self):
        """Child Check has the correct filtered items."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        child = Check(items).first()
        assert len(child._items) == 1
        assert child._items[0]["id"] == 1


# =============================================================================
# TestCheckIntegration - Integration tests
# =============================================================================

class TestCheckIntegration:
    """Integration tests combining multiple Check operations."""

    def test_complex_filtering_chain(self):
        """Complex chain of where() filters works correctly."""
        items = [
            {"type": "message", "text": "hello", "urgent": True},
            {"type": "message", "text": "world", "urgent": False},
            {"type": "typing"},
            {"type": "message", "text": "goodbye", "urgent": True},
        ]
        result = (
            Check(items)
            .where(type="message")
            .where(urgent=True)
            .get()
        )
        assert len(result) == 2
        assert all(item["urgent"] is True for item in result)

    def test_filter_then_assert(self):
        """Filter followed by assertion works correctly."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        Check(items).where(type="message").that(type="message")

    def test_first_then_assert(self):
        """first() followed by assertion works correctly."""
        items = [
            {"type": "message", "text": "first"},
            {"type": "message", "text": "second"},
        ]
        Check(items).first().that(text="first")

    def test_last_then_assert(self):
        """last() followed by assertion works correctly."""
        items = [
            {"type": "message", "text": "first"},
            {"type": "message", "text": "last"},
        ]
        Check(items).last().that(text="last")

    def test_pydantic_model_workflow(self):
        """Full workflow with Pydantic models."""
        items = [
            Message(type="message", text="hello", attachments=["file.txt"]),
            Message(type="typing"),
            Message(type="message", text="world"),
        ]
        result = Check(items).where(type="message").cap(1).get_one()
        assert isinstance(result, Message)
        assert result.text == "hello"

    def test_merge_and_filter(self):
        """merge() followed by filter works correctly."""
        batch1 = [{"type": "message", "batch": 1}]
        batch2 = [{"type": "typing", "batch": 2}]
        merged = Check(batch1).merge(Check(batch2))
        result = merged.where(type="message").get()
        assert len(result) == 1
        assert result[0]["batch"] == 1

    def test_filter_assert_count_chain(self):
        """Chain of filter, assert, and count operations."""
        items = [
            {"type": "message", "status": "sent"},
            {"type": "message", "status": "pending"},
            {"type": "message", "status": "sent"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message")
        assert check.count() == 3
        check.that_for_exactly(2, status="sent")

    def test_where_not_then_that_for_none(self):
        """where_not() combined with that_for_none()."""
        items = [
            {"type": "message", "deleted": False},
            {"type": "message", "deleted": True},
            {"type": "typing", "deleted": False},
        ]
        # Get all non-deleted items and verify none have type "typing" that's also deleted
        Check(items).where_not(deleted=True).that_for_none(deleted=True)

    def test_at_then_assert(self):
        """at() followed by assertion works correctly."""
        items = [
            {"id": 0, "status": "first"},
            {"id": 1, "status": "middle"},
            {"id": 2, "status": "last"},
        ]
        Check(items).at(1).that(status="middle")

    def test_cap_then_that_for_all(self):
        """cap() followed by that_for_all()."""
        items = [
            {"type": "message", "priority": 1},
            {"type": "message", "priority": 2},
            {"type": "message", "priority": 3},
        ]
        Check(items).cap(2).that_for_all(type="message")

    def test_complex_pydantic_assertions(self):
        """Complex assertions on Pydantic models."""
        items = [
            Response(status="success", code=200, data={"id": 1}),
            Response(status="error", code=404),
            Response(status="success", code=201, data={"id": 2}),
        ]
        # Filter to success responses and check they all have 2xx codes
        Check(items).where(status="success").that(
            code=lambda actual: 200 <= actual < 300
        )

    def test_multiple_quantifier_assertions(self):
        """Multiple quantifier-based assertions on same Check."""
        items = [
            {"type": "message", "read": True},
            {"type": "message", "read": False},
            {"type": "message", "read": True},
        ]
        check = Check(items)
        check.that_for_any(read=True)
        check.that_for_any(read=False)
        check.that_for_exactly(2, read=True)
        check.that_for_exactly(1, read=False)


# =============================================================================
# TestCheckEdgeCases - Edge case tests
# =============================================================================

class TestCheckEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_values_in_items(self):
        """Check handles None values in item fields."""
        items = [
            {"type": "message", "text": None},
            {"type": "message", "text": "hello"},
        ]
        check = Check(items).where(text=None)
        assert len(check._items) == 1

    def test_empty_string_field(self):
        """Check handles empty string fields."""
        items = [
            {"type": "message", "text": ""},
            {"type": "message", "text": "hello"},
        ]
        check = Check(items).where(text="")
        assert len(check._items) == 1

    def test_boolean_field_false(self):
        """Check correctly filters on False boolean fields."""
        items = [
            {"active": True},
            {"active": False},
        ]
        check = Check(items).where(active=False)
        assert len(check._items) == 1
        assert check._items[0]["active"] is False

    def test_zero_integer_field(self):
        """Check correctly filters on zero integer fields."""
        items = [
            {"count": 0},
            {"count": 1},
        ]
        check = Check(items).where(count=0)
        assert len(check._items) == 1

    def test_nested_dict_assertion(self):
        """Check handles nested dict assertions."""
        items = [
            {"meta": {"priority": "high", "category": "urgent"}},
        ]
        Check(items).that(meta={"priority": "high", "category": "urgent"})

    def test_list_field_assertion(self):
        """Check handles list field assertions."""
        items = [
            {"tags": ["a", "b", "c"]},
        ]
        Check(items).that(tags=["a", "b", "c"])

    def test_single_item_all_operations(self):
        """All operations work correctly with single item."""
        items = [{"id": 1, "type": "message"}]
        check = Check(items)
        
        assert check.count() == 1
        assert check.exists() is True
        assert check.first().get_one()["id"] == 1
        assert check.last().get_one()["id"] == 1
        assert check.at(0).get_one()["id"] == 1
        check.that(type="message")
        check.that_for_one(type="message")

    def test_large_item_list(self):
        """Check handles large lists efficiently."""
        items = [{"id": i, "type": "message"} for i in range(1000)]
        check = Check(items)
        
        assert check.count() == 1000
        assert check.first().get_one()["id"] == 0
        assert check.last().get_one()["id"] == 999
        assert check.cap(10).count() == 10
        check.that_for_all(type="message")