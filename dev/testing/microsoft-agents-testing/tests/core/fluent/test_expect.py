# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Expect class."""

import pytest
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.expect import Expect


class SampleModel(BaseModel):
    """A sample Pydantic model for testing."""

    name: str
    value: int
    active: bool = True


class TestExpectInit:
    """Tests for Expect initialization."""

    def test_init_with_empty_list(self):
        """Expect initializes with an empty list."""
        expect = Expect([])
        assert expect._items == []

    def test_init_with_dicts(self):
        """Expect initializes with a list of dicts."""
        items = [{"name": "a"}, {"name": "b"}]
        expect = Expect(items)
        assert expect._items == items

    def test_init_with_pydantic_models(self):
        """Expect initializes with a list of Pydantic models."""
        models = [
            SampleModel(name="a", value=1),
            SampleModel(name="b", value=2),
        ]
        expect = Expect(models)
        assert expect._items == models

    def test_init_with_generator(self):
        """Expect materializes a generator to a list."""
        gen = ({"name": x} for x in ["a", "b", "c"])
        expect = Expect(gen)
        assert len(expect._items) == 3


class TestExpectThat:
    """Tests for the that() method (for_all quantifier)."""

    def test_that_all_match_dict_criteria(self):
        """that() passes when all items match dict criteria."""
        items = [{"type": "message"}, {"type": "message"}]
        expect = Expect(items).that(type="message")
        assert expect._items == items

    def test_that_fails_when_not_all_match(self):
        """that() raises AssertionError when not all items match."""
        items = [{"type": "message"}, {"type": "typing"}]
        with pytest.raises(AssertionError) as exc_info:
            Expect(items).that(type="message")
        assert "Expectation failed" in str(exc_info.value)

    def test_that_with_callable(self):
        """that() works with a callable predicate."""
        items = [{"value": 10}, {"value": 20}]
        Expect(items).that(value=lambda x: x > 5)

    def test_that_with_callable_fails(self):
        """that() raises AssertionError when callable fails."""
        items = [{"value": 10}, {"value": 2}]
        with pytest.raises(AssertionError):
            Expect(items).that(value=lambda x: x > 5)

    def test_that_returns_self_for_chaining(self):
        """that() returns self for method chaining."""
        items = [{"type": "message", "text": "hello"}]
        result = Expect(items).that(type="message").that(text="hello")
        assert result._items == items

    def test_that_empty_list_passes(self):
        """that() passes for empty list (vacuous truth)."""
        expect = Expect([]).that(type="message")
        assert expect._items == []


class TestExpectThatForAny:
    """Tests for the that_for_any() method."""

    def test_that_for_any_passes_when_one_matches(self):
        """that_for_any() passes when at least one item matches."""
        items = [{"type": "message"}, {"type": "typing"}]
        Expect(items).that_for_any(type="message")

    def test_that_for_any_passes_when_all_match(self):
        """that_for_any() passes when all items match."""
        items = [{"type": "message"}, {"type": "message"}]
        Expect(items).that_for_any(type="message")

    def test_that_for_any_fails_when_none_match(self):
        """that_for_any() raises AssertionError when no items match."""
        items = [{"type": "typing"}, {"type": "typing"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_any(type="message")

    def test_that_for_any_empty_list_fails(self):
        """that_for_any() fails for empty list."""
        with pytest.raises(AssertionError):
            Expect([]).that_for_any(type="message")


class TestExpectThatForAll:
    """Tests for the that_for_all() method."""

    def test_that_for_all_is_alias_of_that(self):
        """that_for_all() behaves identically to that()."""
        items = [{"type": "message"}, {"type": "message"}]
        Expect(items).that_for_all(type="message")

    def test_that_for_all_fails_when_not_all_match(self):
        """that_for_all() raises AssertionError when not all match."""
        items = [{"type": "message"}, {"type": "typing"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_all(type="message")


class TestExpectThatForNone:
    """Tests for the that_for_none() method."""

    def test_that_for_none_passes_when_none_match(self):
        """that_for_none() passes when no items match."""
        items = [{"type": "typing"}, {"type": "event"}]
        Expect(items).that_for_none(type="message")

    def test_that_for_none_fails_when_one_matches(self):
        """that_for_none() raises AssertionError when any item matches."""
        items = [{"type": "message"}, {"type": "typing"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_none(type="message")

    def test_that_for_none_fails_when_all_match(self):
        """that_for_none() raises AssertionError when all items match."""
        items = [{"type": "message"}, {"type": "message"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_none(type="message")

    def test_that_for_none_empty_list_passes(self):
        """that_for_none() passes for empty list."""
        Expect([]).that_for_none(type="message")


class TestExpectThatForOne:
    """Tests for the that_for_one() method."""

    def test_that_for_one_passes_when_exactly_one_matches(self):
        """that_for_one() passes when exactly one item matches."""
        items = [{"type": "message"}, {"type": "typing"}]
        Expect(items).that_for_one(type="message")

    def test_that_for_one_fails_when_none_match(self):
        """that_for_one() raises AssertionError when no items match."""
        items = [{"type": "typing"}, {"type": "event"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_one(type="message")

    def test_that_for_one_fails_when_multiple_match(self):
        """that_for_one() raises AssertionError when multiple items match."""
        items = [{"type": "message"}, {"type": "message"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_one(type="message")

    def test_that_for_one_empty_list_fails(self):
        """that_for_one() fails for empty list."""
        with pytest.raises(AssertionError):
            Expect([]).that_for_one(type="message")


class TestExpectThatForExactly:
    """Tests for the that_for_exactly() method."""

    def test_that_for_exactly_zero_passes_when_none_match(self):
        """that_for_exactly(0) passes when no items match."""
        items = [{"type": "typing"}, {"type": "event"}]
        Expect(items).that_for_exactly(0, type="message")

    def test_that_for_exactly_two_passes_when_two_match(self):
        """that_for_exactly(2) passes when exactly two items match."""
        items = [{"type": "message"}, {"type": "typing"}, {"type": "message"}]
        Expect(items).that_for_exactly(2, type="message")

    def test_that_for_exactly_fails_when_count_mismatch(self):
        """that_for_exactly() raises AssertionError when count doesn't match."""
        items = [{"type": "message"}, {"type": "message"}]
        with pytest.raises(AssertionError):
            Expect(items).that_for_exactly(1, type="message")

    def test_that_for_exactly_three_matches_all(self):
        """that_for_exactly(3) passes when all three items match."""
        items = [{"type": "message"}] * 3
        Expect(items).that_for_exactly(3, type="message")


class TestExpectIsEmpty:
    """Tests for the is_empty() method."""

    def test_is_empty_passes_for_empty_list(self):
        """is_empty() passes when there are no items."""
        Expect([]).is_empty()

    def test_is_empty_fails_for_non_empty_list(self):
        """is_empty() raises AssertionError when there are items."""
        with pytest.raises(AssertionError) as exc_info:
            Expect([{"a": 1}]).is_empty()
        assert "Expected no items, found 1" in str(exc_info.value)

    def test_is_empty_returns_self(self):
        """is_empty() returns self for chaining."""
        result = Expect([]).is_empty()
        assert isinstance(result, Expect)


class TestExpectIsNotEmpty:
    """Tests for the is_not_empty() method."""

    def test_is_not_empty_passes_for_non_empty_list(self):
        """is_not_empty() passes when there are items."""
        Expect([{"a": 1}]).is_not_empty()

    def test_is_not_empty_fails_for_empty_list(self):
        """is_not_empty() raises AssertionError when there are no items."""
        with pytest.raises(AssertionError) as exc_info:
            Expect([]).is_not_empty()
        assert "Expected some items, found none" in str(exc_info.value)

    def test_is_not_empty_returns_self(self):
        """is_not_empty() returns self for chaining."""
        result = Expect([{"a": 1}]).is_not_empty()
        assert isinstance(result, Expect)


class TestExpectChaining:
    """Tests for method chaining."""

    def test_chain_multiple_assertions(self):
        """Multiple assertions can be chained."""
        items = [{"type": "message", "text": "hello"}]
        Expect(items).is_not_empty().that(type="message").that(text="hello")

    def test_chain_with_different_quantifiers(self):
        """Different quantifier methods can be chained."""
        items = [
            {"type": "message", "active": True},
            {"type": "typing", "active": True},
        ]
        Expect(items).that_for_any(type="message").that_for_all(active=True)


class TestExpectWithPydanticModels:
    """Tests for Expect with Pydantic models."""

    def test_that_with_pydantic_field_match(self):
        """that() works with Pydantic model fields."""
        models = [
            SampleModel(name="test", value=42),
            SampleModel(name="test", value=100),
        ]
        Expect(models).that(name="test")

    def test_that_with_pydantic_callable(self):
        """that() works with callable on Pydantic model fields."""
        models = [
            SampleModel(name="a", value=10),
            SampleModel(name="b", value=20),
        ]
        Expect(models).that(value=lambda x: x > 5)

    def test_that_fails_with_pydantic_mismatch(self):
        """that() raises AssertionError for Pydantic field mismatch."""
        models = [
            SampleModel(name="test", value=42),
            SampleModel(name="other", value=100),
        ]
        with pytest.raises(AssertionError):
            Expect(models).that(name="test")


class TestExpectNestedFields:
    """Tests for Expect with nested fields."""

    def test_that_with_nested_dict(self):
        """that() works with nested dict fields using dot notation."""
        items = [{"user": {"name": "alice"}}, {"user": {"name": "alice"}}]
        Expect(items).that(**{"user.name": "alice"})

    def test_that_with_nested_mismatch(self):
        """that() fails with nested dict field mismatch."""
        items = [{"user": {"name": "alice"}}, {"user": {"name": "bob"}}]
        with pytest.raises(AssertionError):
            Expect(items).that(**{"user.name": "alice"})
