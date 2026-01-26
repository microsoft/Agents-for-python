"""
Unit tests for the Check class.

This module tests:
- Check initialization
- Selector methods (where, where_not, order_by, first, last, at, sample, merge)
- Assertion methods (that, that_for_any, that_for_all, that_for_none, that_for_one, that_for_exactly)
- Terminal operations (get, count, empty, is_empty, is_not_empty)
"""

import pytest
from pydantic import BaseModel
from microsoft_agents.testing.check.check import Check


# =============================================================================
# Test Models
# =============================================================================

class Message(BaseModel):
    type: str
    text: str
    priority: int = 0


class Response(BaseModel):
    status: str
    data: dict = {}


# =============================================================================
# Check Initialization Tests
# =============================================================================

class TestCheckInit:
    """Test Check initialization."""
    
    def test_init_with_list_of_dicts(self):
        items = [{"type": "a"}, {"type": "b"}]
        c = Check(items)
        assert c.count() == 2
    
    def test_init_with_list_of_models(self):
        items = [Message(type="msg", text="hello"), Message(type="msg", text="world")]
        c = Check(items)
        assert c.count() == 2
    
    def test_init_with_empty_list(self):
        c = Check([])
        assert c.count() == 0
    
    def test_init_with_generator(self):
        gen = ({"x": i} for i in range(5))
        c = Check(gen)
        assert c.count() == 5
    
    def test_init_converts_to_list(self):
        items = [{"a": 1}, {"b": 2}]
        c = Check(items)
        assert isinstance(c._items, list)


# =============================================================================
# Where Selector Tests
# =============================================================================

class TestWhereSelector:
    """Test the where selector method."""
    
    def test_where_with_kwargs(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing", "text": ""},
            {"type": "message", "text": "world"},
        ]
        c = Check(items).where(type="message")
        assert c.count() == 2
    
    def test_where_with_dict_filter(self):
        items = [
            {"type": "message", "text": "hello"},
            {"type": "typing", "text": ""},
        ]
        c = Check(items).where({"type": "message"})
        assert c.count() == 1
    
    def test_where_no_matches(self):
        items = [{"type": "a"}, {"type": "b"}]
        c = Check(items).where(type="c")
        assert c.count() == 0
    
    def test_where_all_match(self):
        items = [{"type": "a"}, {"type": "a"}]
        c = Check(items).where(type="a")
        assert c.count() == 2
    
    def test_where_chained(self):
        items = [
            {"type": "message", "priority": 1},
            {"type": "message", "priority": 2},
            {"type": "typing", "priority": 1},
        ]
        c = Check(items).where(type="message").where(priority=1)
        assert c.count() == 1
    
    def test_where_with_callable(self):
        items = [{"value": 1}, {"value": 5}, {"value": 10}]
        c = Check(items).where(value=lambda actual: actual > 3)
        assert c.count() == 2


# =============================================================================
# Where Not Selector Tests
# =============================================================================

class TestWhereNotSelector:
    """Test the where_not selector method."""
    
    def test_where_not_excludes_matches(self):
        items = [
            {"type": "message"},
            {"type": "typing"},
            {"type": "message"},
        ]
        c = Check(items).where_not(type="message")
        assert c.count() == 1
    
    def test_where_not_no_exclusions(self):
        items = [{"type": "a"}, {"type": "b"}]
        c = Check(items).where_not(type="c")
        assert c.count() == 2
    
    def test_where_not_all_excluded(self):
        items = [{"type": "a"}, {"type": "a"}]
        c = Check(items).where_not(type="a")
        assert c.count() == 0


# =============================================================================
# Order By Selector Tests
# =============================================================================

class TestOrderBySelector:
    """Test the order_by selector method."""
    
    def test_order_by_string_key(self):
        items = [{"priority": 3}, {"priority": 1}, {"priority": 2}]
        c = Check(items).order_by("priority")
        result = c.get()
        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 3
    
    def test_order_by_reverse(self):
        items = [{"priority": 1}, {"priority": 3}, {"priority": 2}]
        c = Check(items).order_by("priority", reverse=True)
        result = c.get()
        assert result[0]["priority"] == 3
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 1
    
    def test_order_by_callable(self):
        items = [{"name": "cc"}, {"name": "a"}, {"name": "bbb"}]
        c = Check(items).order_by(key=lambda actual: len(actual["name"]))
        result = c.get()
        assert result[0]["name"] == "a"
        assert result[1]["name"] == "cc"
        assert result[2]["name"] == "bbb"


# =============================================================================
# First/Last/At Selector Tests
# =============================================================================

class TestPositionalSelectors:
    """Test first, last, and at selectors."""
    
    def test_first_default(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).first()
        assert c.count() == 1
        assert c.get()[0]["id"] == 1
    
    def test_first_n(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).first(2)
        assert c.count() == 2
        assert c.get()[0]["id"] == 1
        assert c.get()[1]["id"] == 2
    
    def test_last_default(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).last()
        assert c.count() == 1
        assert c.get()[0]["id"] == 3
    
    def test_last_n(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).last(2)
        assert c.count() == 2
        assert c.get()[0]["id"] == 2
        assert c.get()[1]["id"] == 3
    
    def test_at_index(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).at(1)
        assert c.count() == 1
        assert c.get()[0]["id"] == 2
    
    def test_at_first(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).at(0)
        assert c.get()[0]["id"] == 1
    
    def test_at_last(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items).at(2)
        assert c.get()[0]["id"] == 3


# =============================================================================
# Sample Selector Tests
# =============================================================================

class TestSampleSelector:
    """Test the sample selector."""
    
    def test_sample_returns_n_items(self):
        items = [{"id": i} for i in range(10)]
        c = Check(items).sample(3)
        assert c.count() == 3
    
    def test_sample_more_than_available(self):
        items = [{"id": 1}, {"id": 2}]
        c = Check(items).sample(10)
        assert c.count() == 2
    
    def test_sample_zero(self):
        items = [{"id": 1}, {"id": 2}]
        c = Check(items).sample(0)
        assert c.count() == 0
    
    def test_sample_negative_raises(self):
        items = [{"id": 1}]
        with pytest.raises(ValueError):
            Check(items).sample(-1)


# =============================================================================
# Merge Selector Tests
# =============================================================================

class TestMergeSelector:
    """Test the merge selector."""
    
    def test_merge_two_checks(self):
        c1 = Check([{"id": 1}, {"id": 2}])
        c2 = Check([{"id": 3}, {"id": 4}])
        merged = c1.merge(c2)
        assert merged.count() == 4
    
    def test_merge_preserves_order(self):
        c1 = Check([{"id": 1}])
        c2 = Check([{"id": 2}])
        merged = c1.merge(c2)
        result = merged.get()
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
    
    def test_merge_with_empty(self):
        c1 = Check([{"id": 1}])
        c2 = Check([])
        merged = c1.merge(c2)
        assert merged.count() == 1


# =============================================================================
# Assertion Tests
# =============================================================================

class TestThatAssertion:
    """Test the that assertion method."""
    
    def test_that_passes(self):
        items = [{"type": "a"}, {"type": "a"}]
        Check(items).that(type="a")  # Should not raise
    
    def test_that_fails(self):
        items = [{"type": "a"}, {"type": "b"}]
        with pytest.raises(AssertionError):
            Check(items).that(type="a")


class TestThatForAnyAssertion:
    """Test the that_for_any assertion method."""
    
    def test_that_for_any_passes(self):
        items = [{"type": "a"}, {"type": "b"}]
        Check(items).that_for_any(type="a")  # Should not raise
    
    def test_that_for_any_fails(self):
        items = [{"type": "b"}, {"type": "b"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_any(type="a")


class TestThatForAllAssertion:
    """Test the that_for_all assertion method."""
    
    def test_that_for_all_passes(self):
        items = [{"type": "a"}, {"type": "a"}]
        Check(items).that_for_all(type="a")  # Should not raise
    
    def test_that_for_all_fails(self):
        items = [{"type": "a"}, {"type": "b"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_all(type="a")


class TestThatForNoneAssertion:
    """Test the that_for_none assertion method."""
    
    def test_that_for_none_passes(self):
        items = [{"type": "b"}, {"type": "c"}]
        Check(items).that_for_none(type="a")  # Should not raise
    
    def test_that_for_none_fails(self):
        items = [{"type": "a"}, {"type": "b"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_none(type="a")


class TestThatForOneAssertion:
    """Test the that_for_one assertion method."""
    
    def test_that_for_one_passes(self):
        items = [{"type": "a"}, {"type": "b"}, {"type": "b"}]
        Check(items).that_for_one(type="a")  # Should not raise
    
    def test_that_for_one_fails_none(self):
        items = [{"type": "b"}, {"type": "b"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_one(type="a")
    
    def test_that_for_one_fails_multiple(self):
        items = [{"type": "a"}, {"type": "a"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_one(type="a")


class TestThatForExactlyAssertion:
    """Test the that_for_exactly assertion method."""
    
    def test_that_for_exactly_passes(self):
        items = [{"type": "a"}, {"type": "a"}, {"type": "b"}]
        Check(items).that_for_exactly(2, type="a")  # Should not raise
    
    def test_that_for_exactly_fails(self):
        items = [{"type": "a"}, {"type": "a"}, {"type": "a"}]
        with pytest.raises(AssertionError):
            Check(items).that_for_exactly(2, type="a")


# =============================================================================
# Is Empty/Is Not Empty Tests
# =============================================================================

class TestIsEmptyAssertions:
    """Test is_empty and is_not_empty assertions."""
    
    def test_is_empty_passes(self):
        c = Check([])
        c.is_empty()  # Should not raise
    
    def test_is_empty_fails(self):
        c = Check([{"id": 1}])
        with pytest.raises(AssertionError):
            c.is_empty()
    
    def test_is_not_empty_passes(self):
        c = Check([{"id": 1}])
        c.is_not_empty()  # Should not raise
    
    def test_is_not_empty_fails(self):
        c = Check([])
        with pytest.raises(AssertionError):
            c.is_not_empty()


# =============================================================================
# Terminal Operations Tests
# =============================================================================

class TestTerminalOperations:
    """Test terminal operations."""
    
    def test_get_returns_list(self):
        items = [{"id": 1}, {"id": 2}]
        c = Check(items)
        result = c.get()
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_count_returns_int(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        c = Check(items)
        assert c.count() == 3
    
    def test_empty_returns_bool(self):
        assert Check([]).empty() is True
        assert Check([{"id": 1}]).empty() is False


# =============================================================================
# Chaining Tests
# =============================================================================

class TestChaining:
    """Test method chaining."""
    
    def test_where_then_first(self):
        items = [
            {"type": "a", "id": 1},
            {"type": "a", "id": 2},
            {"type": "b", "id": 3},
        ]
        c = Check(items).where(type="a").first()
        assert c.count() == 1
        assert c.get()[0]["id"] == 1
    
    def test_where_then_order_by(self):
        items = [
            {"type": "a", "priority": 2},
            {"type": "a", "priority": 1},
            {"type": "b", "priority": 3},
        ]
        c = Check(items).where(type="a").order_by("priority")
        result = c.get()
        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
    
    def test_complex_chain(self):
        items = [
            {"type": "msg", "priority": 1, "text": "hello"},
            {"type": "msg", "priority": 2, "text": "world"},
            {"type": "typing", "priority": 1, "text": ""},
            {"type": "msg", "priority": 3, "text": "!"},
        ]
        c = (Check(items)
             .where(type="msg")
             .order_by("priority", reverse=True)
             .first(2))
        assert c.count() == 2
        result = c.get()
        assert result[0]["priority"] == 3
        assert result[1]["priority"] == 2


# =============================================================================
# Pydantic Model Tests
# =============================================================================

class TestPydanticModels:
    """Test Check with Pydantic models."""
    
    def test_with_pydantic_models(self):
        items = [
            Message(type="msg", text="hello", priority=1),
            Message(type="msg", text="world", priority=2),
        ]
        c = Check(items)
        assert c.count() == 2
    
    def test_where_on_pydantic(self):
        items = [
            Message(type="msg", text="hello", priority=1),
            Message(type="typing", text="", priority=0),
        ]
        c = Check(items).where(type="msg")
        assert c.count() == 1
