# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for typed fluent activity and exchange wrappers."""

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core import (
    ActivityExpect,
    ActivitySelect,
    Exchange,
    ExchangeExpect,
    ExchangeSelect,
)


def _message(text: str) -> Activity:
    return Activity(type=ActivityTypes.message, text=text)


def _exchange(text: str, status_code: int = 200) -> Exchange:
    return Exchange(
        request=_message(text),
        status_code=status_code,
        responses=[_message(f"Reply: {text}")],
    )


class TestActivityExpect:
    """Tests for ActivityExpect."""

    def test_asserts_over_activity_fields(self):
        """ActivityExpect can assert directly on Activity fields."""
        expect = ActivityExpect([_message("Hello"), _message("Hi")])

        result = expect.that_for_all(type=ActivityTypes.message).that_for_any(
            text="Hello"
        )

        assert result is expect

    def test_fails_when_activity_criteria_do_not_match(self):
        """ActivityExpect raises when activity criteria fail."""
        expect = ActivityExpect([Activity(type=ActivityTypes.typing)])

        try:
            expect.that_for_any(type=ActivityTypes.message)
        except AssertionError as error:
            assert "Expectation failed" in str(error)
        else:
            raise AssertionError("Expected ActivityExpect to fail.")


class TestActivitySelect:
    """Tests for ActivitySelect."""

    def test_filters_activities_and_preserves_activity_select_type(self):
        """ActivitySelect filters Activity items and returns ActivitySelect children."""
        activities = [
            _message("First"),
            Activity(type=ActivityTypes.typing),
            _message("Second"),
        ]

        selected = ActivitySelect(activities).where(type=ActivityTypes.message)

        assert isinstance(selected, ActivitySelect)
        assert [activity.text for activity in selected.get()] == ["First", "Second"]

    def test_expect_returns_activity_expect(self):
        """ActivitySelect.expect() returns ActivityExpect."""
        selected = ActivitySelect([_message("Hello")])

        expect = selected.expect()

        assert isinstance(expect, ActivityExpect)
        expect.that_for_one(text="Hello")


class TestExchangeExpect:
    """Tests for ExchangeExpect."""

    def test_asserts_over_exchange_fields(self):
        """ExchangeExpect can assert directly on Exchange fields."""
        expect = ExchangeExpect([_exchange("Hello", 200), _exchange("Fail", 500)])

        result = expect.that_for_any(status_code=200).that_for_any(status_code=500)

        assert result is expect

    def test_fails_when_exchange_criteria_do_not_match(self):
        """ExchangeExpect raises when exchange criteria fail."""
        expect = ExchangeExpect([_exchange("Hello", 200)])

        try:
            expect.that_for_any(status_code=500)
        except AssertionError as error:
            assert "Expectation failed" in str(error)
        else:
            raise AssertionError("Expected ExchangeExpect to fail.")


class TestExchangeSelect:
    """Tests for ExchangeSelect."""

    def test_filters_exchanges_and_preserves_exchange_select_type(self):
        """ExchangeSelect filters Exchange items and returns ExchangeSelect children."""
        exchanges = [_exchange("OK", 200), _exchange("Created", 201)]

        selected = ExchangeSelect(exchanges).where(status_code=200)

        assert isinstance(selected, ExchangeSelect)
        assert [exchange.request.text for exchange in selected.get()] == ["OK"]

    def test_expect_returns_exchange_expect(self):
        """ExchangeSelect.expect() returns ExchangeExpect."""
        selected = ExchangeSelect([_exchange("OK", 200)])

        expect = selected.expect()

        assert isinstance(expect, ExchangeExpect)
        expect.that_for_one(status_code=200)

