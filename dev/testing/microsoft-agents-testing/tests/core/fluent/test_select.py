# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Select class."""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.select import Select
from microsoft_agents.testing.core.fluent.expect import Expect


class SampleModel(BaseModel):
    """A sample Pydantic model for testing."""

    name: str
    value: int
    active: bool = True


class TestSelectInit:
    """Tests for Select initialization."""

    def test_init_with_empty_list(self):
        """Select initializes with an empty list."""
        select = Select([])
        assert select._items == []

    def test_init_with_dicts(self):
        """Select initializes with a list of dicts."""
        items = [{"name": "a"}, {"name": "b"}]
        select = Select(items)
        assert select._items == items

    def test_init_with_pydantic_models(self):
        """Select initializes with a list of Pydantic models."""
        models = [
            SampleModel(name="a", value=1),
            SampleModel(name="b", value=2),
        ]
        select = Select(models)
        assert select._items == models

    def test_init_with_generator(self):
        """Select materializes a generator to a list."""
        gen = ({"name": x} for x in ["a", "b", "c"])
        select = Select(gen)
        assert len(select._items) == 3


class TestSelectExpect:
    """Tests for the expect() method."""

    def test_expect_returns_expect_instance(self):
        """expect() returns an Expect instance."""
        select = Select([{"name": "a"}])
        result = select.expect()
        assert isinstance(result, Expect)

    def test_expect_with_correct_items(self):
        """expect() passes the current items to Expect."""
        items = [{"name": "a"}, {"name": "b"}]
        select = Select(items)
        expect = select.expect()
        assert expect._items == items


class TestSelectWhere:
    """Tests for the where() method."""

    def test_where_filters_by_dict_criteria(self):
        """where() filters items by dict criteria."""
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing"},
            {"type": "message", "text": "world"},
        ]
        result = Select(items).where({"type": "message"}).get()
        assert len(result) == 2
        assert all(item["type"] == "message" for item in result)

    def test_where_filters_by_kwargs(self):
        """where() filters items by keyword arguments."""
        items = [
            {"name": "alice", "active": True},
            {"name": "bob", "active": False},
            {"name": "charlie", "active": True},
        ]
        result = Select(items).where(None, active=True).get()
        assert len(result) == 2

    def test_where_filters_by_callable(self):
        """where() filters items by callable predicate."""
        items = [
            {"name": "a", "value": 10},
            {"name": "b", "value": 5},
            {"name": "c", "value": 20},
        ]
        result = Select(items).where({"value": lambda x: x > 7}).get()
        assert len(result) == 2

    def test_where_returns_select(self):
        """where() returns a Select instance for chaining."""
        result = Select([{"a": 1}]).where({"a": 1})
        assert isinstance(result, Select)

    def test_where_empty_result(self):
        """where() returns empty Select when nothing matches."""
        items = [{"type": "message"}]
        result = Select(items).where({"type": "typing"}).get()
        assert result == []

    def test_where_chaining(self):
        """where() can be chained multiple times."""
        items = [
            {"type": "message", "active": True},
            {"type": "message", "active": False},
            {"type": "typing", "active": True},
        ]
        result = Select(items).where({"type": "message"}).where(None, active=True).get()
        assert len(result) == 1


class TestSelectWhereNot:
    """Tests for the where_not() method."""

    def test_where_not_excludes_by_criteria(self):
        """where_not() excludes items matching criteria."""
        items = [
            {"type": "message"},
            {"type": "typing"},
            {"type": "event"},
        ]
        result = Select(items).where_not({"type": "message"}).get()
        assert len(result) == 2
        assert all(item["type"] != "message" for item in result)

    def test_where_not_with_callable(self):
        """where_not() excludes items matching callable."""
        items = [
            {"value": 10},
            {"value": 5},
            {"value": 20},
        ]
        result = Select(items).where_not({"value": lambda x: x > 15}).get()
        assert len(result) == 2

    def test_where_not_excludes_nothing(self):
        """where_not() returns all items when nothing matches."""
        items = [{"type": "message"}, {"type": "message"}]
        result = Select(items).where_not({"type": "typing"}).get()
        assert len(result) == 2


class TestSelectFirst:
    """Tests for the first() method."""

    def test_first_returns_first_item(self):
        """first() returns the first item."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).first().get()
        assert len(result) == 1
        assert result[0]["name"] == "a"

    def test_first_with_n(self):
        """first(n) returns the first n items."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).first(2).get()
        assert len(result) == 2
        assert result[0]["name"] == "a"
        assert result[1]["name"] == "b"

    def test_first_with_n_greater_than_length(self):
        """first(n) returns all items when n > length."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).first(5).get()
        assert len(result) == 2

    def test_first_on_empty_list(self):
        """first() returns empty list when no items."""
        result = Select([]).first().get()
        assert result == []


class TestSelectLast:
    """Tests for the last() method."""

    def test_last_returns_last_item(self):
        """last() returns the last item."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).last().get()
        assert len(result) == 1
        assert result[0]["name"] == "c"

    def test_last_with_n(self):
        """last(n) returns the last n items."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).last(2).get()
        assert len(result) == 2
        assert result[0]["name"] == "b"
        assert result[1]["name"] == "c"

    def test_last_with_n_greater_than_length(self):
        """last(n) returns all items when n > length."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).last(5).get()
        assert len(result) == 2

    def test_last_on_empty_list(self):
        """last() returns empty list when no items."""
        result = Select([]).last().get()
        assert result == []


class TestSelectAt:
    """Tests for the at() method."""

    def test_at_returns_item_at_index(self):
        """at() returns item at the specified index."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).at(1).get()
        assert len(result) == 1
        assert result[0]["name"] == "b"

    def test_at_first_index(self):
        """at(0) returns the first item."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).at(0).get()
        assert result[0]["name"] == "a"

    def test_at_last_index(self):
        """at() returns item at last index."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = Select(items).at(2).get()
        assert result[0]["name"] == "c"

    def test_at_out_of_range(self):
        """at() returns empty list when index out of range."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).at(5).get()
        assert result == []


class TestSelectSample:
    """Tests for the sample() method."""

    def test_sample_returns_n_items(self):
        """sample() returns n random items."""
        items = [{"name": str(i)} for i in range(10)]
        result = Select(items).sample(3).get()
        assert len(result) == 3

    def test_sample_returns_all_when_n_exceeds_length(self):
        """sample() returns all items when n > length."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).sample(10).get()
        assert len(result) == 2

    def test_sample_returns_empty_for_n_zero(self):
        """sample(0) returns empty list."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).sample(0).get()
        assert result == []

    def test_sample_raises_for_negative_n(self):
        """sample() raises ValueError for negative n."""
        with pytest.raises(ValueError, match="non-negative"):
            Select([{"a": 1}]).sample(-1)


class TestSelectMerge:
    """Tests for the merge() method."""

    def test_merge_combines_items(self):
        """merge() combines items from two selects."""
        select1 = Select([{"name": "a"}])
        select2 = Select([{"name": "b"}])
        result = select1.merge(select2).get()
        assert len(result) == 2

    def test_merge_preserves_order(self):
        """merge() preserves order (first select, then other)."""
        select1 = Select([{"name": "a"}, {"name": "b"}])
        select2 = Select([{"name": "c"}])
        result = select1.merge(select2).get()
        assert [item["name"] for item in result] == ["a", "b", "c"]

    def test_merge_with_empty_other(self):
        """merge() with empty other returns original items."""
        select1 = Select([{"name": "a"}])
        select2 = Select([])
        result = select1.merge(select2).get()
        assert len(result) == 1


class TestSelectTerminalOperations:
    """Tests for terminal operations."""

    def test_get_returns_items_list(self):
        """get() returns the items as a list."""
        items = [{"name": "a"}, {"name": "b"}]
        result = Select(items).get()
        assert result == items

    def test_count_returns_item_count(self):
        """count() returns the number of items."""
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        assert Select(items).count() == 3

    def test_count_empty(self):
        """count() returns 0 for empty select."""
        assert Select([]).count() == 0

    def test_empty_returns_true_for_empty(self):
        """empty() returns True when no items."""
        assert Select([]).empty() is True

    def test_empty_returns_false_for_non_empty(self):
        """empty() returns False when items exist."""
        assert Select([{"a": 1}]).empty() is False


class TestSelectWithPydanticModels:
    """Tests for Select with Pydantic models."""

    def test_where_with_pydantic_models(self):
        """where() works with Pydantic models."""
        models = [
            SampleModel(name="alice", value=10),
            SampleModel(name="bob", value=20),
            SampleModel(name="charlie", value=10),
        ]
        result = Select(models).where({"value": 10}).get()
        assert len(result) == 2

    def test_where_with_callable_on_pydantic(self):
        """where() with callable works on Pydantic models."""
        models = [
            SampleModel(name="a", value=5),
            SampleModel(name="b", value=15),
            SampleModel(name="c", value=25),
        ]
        result = Select(models).where({"value": lambda x: x > 10}).get()
        assert len(result) == 2


class TestSelectChaining:
    """Tests for complex chaining scenarios."""

    def test_chain_where_first(self):
        """where() followed by first() works correctly."""
        items = [
            {"type": "a", "order": 1},
            {"type": "b", "order": 2},
            {"type": "a", "order": 3},
        ]
        result = Select(items).where({"type": "a"}).first().get()
        assert len(result) == 1
        assert result[0]["order"] == 1

    def test_chain_where_last(self):
        """where() followed by last() works correctly."""
        items = [
            {"type": "a", "order": 1},
            {"type": "b", "order": 2},
            {"type": "a", "order": 3},
        ]
        result = Select(items).where({"type": "a"}).last().get()
        assert len(result) == 1
        assert result[0]["order"] == 3

    def test_chain_multiple_operations(self):
        """Multiple operations can be chained together."""
        items = [{"v": i} for i in range(10)]
        result = Select(items).where({"v": lambda x: x > 3}).first(3).get()
        assert len(result) == 3
        assert [item["v"] for item in result] == [4, 5, 6]


class TestSelectNestedFields:
    """Tests for Select with nested fields."""

    def test_where_with_nested_dict_field(self):
        """where() works with nested dict fields using dot notation."""
        items = [
            {"user": {"name": "alice", "age": 30}},
            {"user": {"name": "bob", "age": 25}},
            {"user": {"name": "charlie", "age": 35}},
        ]
        result = Select(items).where(None, **{"user.name": "alice"}).get()
        assert len(result) == 1

    def test_where_with_nested_callable(self):
        """where() with callable works on nested fields."""
        items = [
            {"data": {"value": 10}},
            {"data": {"value": 20}},
            {"data": {"value": 5}},
        ]
        result = Select(items).where(None, **{"data.value": lambda x: x > 8}).get()
        assert len(result) == 2
