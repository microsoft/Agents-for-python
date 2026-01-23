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


class Message(BaseModel):
    type: str
    text: str | None = None
    attachments: list[str] | None = None


class TestCheckInit:
    """Test Check initialization."""

    def test_init_with_empty_list(self):
        check = Check([])
        assert check._items == []
        assert check._quantifier is for_all

    def test_init_with_dict_items(self):
        items = [{"type": "message", "text": "hello"}]
        check = Check(items)
        assert check._items == items
        assert check._quantifier is for_all

    def test_init_with_pydantic_models(self):
        items = [Message(type="message", text="hello")]
        check = Check(items)
        assert len(check._items) == 1
        assert check._items[0].type == "message"

    def test_init_with_custom_quantifier(self):
        items = [{"type": "message"}]
        check = Check(items, quantifier=for_any)
        assert check._quantifier is for_any

    def test_init_converts_iterable_to_list(self):
        items = iter([{"type": "message"}, {"type": "typing"}])
        check = Check(items)
        assert isinstance(check._items, list)
        assert len(check._items) == 2


class TestCheckWhere:
    """Test Check.where() filtering."""

    def test_where_filters_by_single_field(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        check = Check(items).where(type="message")
        assert len(check._items) == 2
        assert all(item["type"] == "message" for item in check._items)

    def test_where_filters_by_multiple_fields(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message", text="hello")
        assert len(check._items) == 1
        assert check._items[0]["text"] == "hello"

    def test_where_with_dict_filter(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
        ]
        check = Check(items).where({"type": "message"})
        assert len(check._items) == 1
        assert check._items[0]["type"] == "message"

    def test_where_returns_empty_when_no_match(self):
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        check = Check(items).where(type="unknown")
        assert len(check._items) == 0

    def test_where_is_chainable(self):
        items = [
            {"type": "message", "text": "hello", "urgent": True},
            {"type": "message", "text": "world", "urgent": False},
            {"type": "typing"},
        ]
        check = Check(items).where(type="message").where(urgent=True)
        assert len(check._items) == 1
        assert check._items[0]["text"] == "hello"

    def test_where_with_pydantic_models(self):
        items = [
            Message(type="message", text="hello"),
            Message(type="typing"),
            Message(type="message", text="world"),
        ]
        check = Check(items).where(type="message")
        assert len(check._items) == 2


class TestCheckWhereNot:
    """Test Check.where_not() exclusion filtering."""

    def test_where_not_excludes_matching_items(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        check = Check(items).where_not(type="message")
        assert len(check._items) == 1
        assert check._items[0]["type"] == "typing"

    def test_where_not_with_multiple_fields(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="message", text="hello")
        assert len(check._items) == 2

    def test_where_not_returns_all_when_no_match(self):
        items = [
            {"type": "message"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="unknown")
        assert len(check._items) == 2

    def test_where_not_is_chainable(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
            {"type": "typing"},
        ]
        check = Check(items).where_not(type="typing").where_not(text="hello")
        assert len(check._items) == 1
        assert check._items[0]["text"] == "world"


class TestCheckMerge:
    """Test Check.merge() combining checks."""

    def test_merge_combines_items(self):
        items1 = [{"type": "message", "text": "hello"}]
        items2 = [{"type": "typing"}]
        check1 = Check(items1)
        check2 = Check(items2)
        merged = check1.merge(check2)
        assert len(merged._items) == 2

    def test_merge_preserves_order(self):
        items1 = [{"id": 1}, {"id": 2}]
        items2 = [{"id": 3}, {"id": 4}]
        merged = Check(items1).merge(Check(items2))
        assert [item["id"] for item in merged._items] == [1, 2, 3, 4]

    def test_merge_empty_checks(self):
        check1 = Check([])
        check2 = Check([])
        merged = check1.merge(check2)
        assert len(merged._items) == 0


class TestCheckPositionalSelectors:
    """Test Check positional selectors: first(), last(), at(), cap()."""

    def test_first_returns_first_item(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).first()
        assert len(check._items) == 1
        assert check._items[0]["id"] == 1

    def test_first_on_empty_list(self):
        check = Check([]).first()
        assert len(check._items) == 0

    def test_last_returns_last_item(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).last()
        assert len(check._items) == 1
        assert check._items[0]["id"] == 3

    def test_last_on_empty_list(self):
        check = Check([]).last()
        assert len(check._items) == 0

    def test_at_returns_nth_item(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        check = Check(items).at(1)
        assert len(check._items) == 1
        assert check._items[0]["id"] == 2

    def test_at_out_of_bounds(self):
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).at(5)
        assert len(check._items) == 0

    def test_cap_limits_items(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        check = Check(items).cap(2)
        assert len(check._items) == 2
        assert check._items[0]["id"] == 1
        assert check._items[1]["id"] == 2

    def test_cap_with_larger_n_than_items(self):
        items = [{"id": 1}, {"id": 2}]
        check = Check(items).cap(10)
        assert len(check._items) == 2


class TestCheckQuantifiers:
    """Test Check quantifier properties."""

    def test_for_any_sets_quantifier(self):
        check = Check([{"id": 1}]).for_any
        assert check._quantifier is for_any

    def test_for_all_sets_quantifier(self):
        check = Check([{"id": 1}], quantifier=for_any).for_all
        assert check._quantifier is for_all

    def test_for_none_sets_quantifier(self):
        check = Check([{"id": 1}]).for_none
        assert check._quantifier is for_none

    def test_for_one_sets_quantifier(self):
        check = Check([{"id": 1}]).for_one
        assert check._quantifier is for_one

    def test_quantifier_is_chainable_with_selectors(self):
        items = [{"type": "message"}, {"type": "typing"}]
        check = Check(items).for_any.where(type="message")
        assert check._quantifier is for_any
        assert len(check._items) == 1


class TestCheckThat:
    """Test Check.that() assertions."""

    def test_that_passes_when_all_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "hello"},
        ]
        # Should not raise
        Check(items).that(text="hello")

    def test_that_fails_when_not_all_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).that(text="hello")

    def test_that_with_for_any_passes_when_any_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).for_any.that(text="hello")

    def test_that_with_for_any_fails_when_none_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).for_any.that(text="unknown")

    def test_that_with_for_none_passes_when_none_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).for_none.that(text="unknown")

    def test_that_with_for_none_fails_when_any_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        with pytest.raises(AssertionError):
            Check(items).for_none.that(text="hello")

    def test_that_with_for_one_passes_when_exactly_one_matches(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "world"},
        ]
        Check(items).for_one.that(text="hello")

    def test_that_with_for_one_fails_when_multiple_match(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "message", "text": "hello"},
        ]
        with pytest.raises(AssertionError):
            Check(items).for_one.that(text="hello")

    def test_that_with_multiple_criteria(self):
        items = [{"type": "message", "text": "hello", "urgent": True}]
        Check(items).that(type="message", text="hello", urgent=True)

    def test_that_with_dict_assertion(self):
        items = [{"type": "message", "text": "hello"}]
        Check(items).that({"type": "message", "text": "hello"})

    def test_that_with_callable_assertion(self):
        items = [{"type": "message", "count": 5}]
        Check(items).that(count=lambda actual: actual > 3)

    def test_that_after_where_filter(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        Check(items).where(type="message").that(type="message")


class TestCheckTerminalOperations:
    """Test Check terminal operations: get(), get_one(), count(), exists()."""

    def test_get_returns_items_list(self):
        items = [{"id": 1}, {"id": 2}]
        result = Check(items).get()
        assert result == items
        assert isinstance(result, list)

    def test_get_returns_filtered_items(self):
        items = [{"type": "message"}, {"type": "typing"}]
        result = Check(items).where(type="message").get()
        assert len(result) == 1
        assert result[0]["type"] == "message"

    def test_get_one_returns_single_item(self):
        items = [{"id": 1}]
        result = Check(items).get_one()
        assert result == {"id": 1}

    def test_get_one_raises_when_empty(self):
        with pytest.raises(ValueError, match="Expected exactly one item"):
            Check([]).get_one()

    def test_get_one_raises_when_multiple(self):
        items = [{"id": 1}, {"id": 2}]
        with pytest.raises(ValueError, match="Expected exactly one item"):
            Check(items).get_one()

    def test_count_returns_number_of_items(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        assert Check(items).count() == 3

    def test_count_returns_zero_for_empty(self):
        assert Check([]).count() == 0

    def test_count_after_filter(self):
        items = [{"type": "message"}, {"type": "typing"}, {"type": "message"}]
        assert Check(items).where(type="message").count() == 2

    def test_exists_returns_true_when_items_present(self):
        items = [{"id": 1}]
        assert Check(items).exists() is True

    def test_exists_returns_false_when_empty(self):
        assert Check([]).exists() is False

    def test_exists_after_filter(self):
        items = [{"type": "message"}, {"type": "typing"}]
        assert Check(items).where(type="message").exists() is True
        assert Check(items).where(type="unknown").exists() is False


class TestCheckChildInheritance:
    """Test that child Check instances properly inherit engine and state."""

    def test_child_inherits_engine(self):
        check = Check([{"id": 1}])
        child = check.first()
        assert child._engine is check._engine

    def test_child_inherits_quantifier_by_default(self):
        check = Check([{"id": 1}], quantifier=for_any)
        child = check.first()
        assert child._quantifier is for_any

    def test_child_can_override_quantifier(self):
        check = Check([{"id": 1}], quantifier=for_any)
        child = check.for_all
        assert child._quantifier is for_all


class TestCheckIntegration:
    """Integration tests combining multiple Check operations."""

    def test_complex_filtering_chain(self):
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
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        # Filter to messages, then assert all have type="message"
        Check(items).where(type="message").that(type="message")

    def test_first_then_assert(self):
        items = [
            {"type": "message", "text": "first"},
            {"type": "message", "text": "second"},
        ]
        Check(items).first().that(text="first")

    def test_last_then_assert(self):
        items = [
            {"type": "message", "text": "first"},
            {"type": "message", "text": "last"},
        ]
        Check(items).last().that(text="last")

    def test_pydantic_model_workflow(self):
        items = [
            Message(type="message", text="hello", attachments=["file.txt"]),
            Message(type="typing"),
            Message(type="message", text="world"),
        ]
        result = Check(items).where(type="message").cap(1).get_one()
        assert isinstance(result, Message)
        assert result.text == "hello"

    def test_for_any_with_filter_and_assertion(self):
        items = [
            {"type": "message", "status": "sent"},
            {"type": "message", "status": "pending"},
            {"type": "typing"},
        ]
        Check(items).where(type="message").for_any.that(status="sent")

    def test_merge_and_filter(self):
        batch1 = [{"type": "message", "batch": 1}]
        batch2 = [{"type": "typing", "batch": 2}]
        merged = Check(batch1).merge(Check(batch2))
        result = merged.where(type="message").get()
        assert len(result) == 1
        assert result[0]["batch"] == 1