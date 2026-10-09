"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from typing import Any

import pytest
from pydantic import ValidationError
from typing_extensions import assert_type

from microsoft_agents.hosting.slack.api import EventContent, SlackResponse


class TestSlackResponse:
    def test_minimal_ok_true(self):
        r = SlackResponse.model_validate({"ok": True})
        assert r.ok is True
        assert r.error is None

    def test_ok_false_with_error(self):
        r = SlackResponse.model_validate({"ok": False, "error": "not_authed"})
        assert r.ok is False
        assert r.error == "not_authed"

    def test_extra_fields_preserved_via_get(self):
        r = SlackResponse.model_validate(
            {
                "ok": True,
                "ts": "1776.001",
                "channel": "C0001",
                "message": {
                    "ts": "1776.001",
                    "text": "hi",
                    "attachments": [{"text": "alt"}],
                },
            }
        )
        assert r.ts == "1776.001"
        assert r.get("channel") == "C0001"
        assert r.get("message.text") == "hi"
        assert r.get("message.attachments[0].text") == "alt"
        # missing path returns None / default
        assert r.get("nope") is None
        assert r.get("nope", default="x") == "x"

    def test_try_get(self):
        r = SlackResponse.model_validate({"ok": True, "warning": "missing_charset"})
        found, value = r.try_get("warning")
        assert found and value == "missing_charset"
        found, _ = r.try_get("nope")
        assert not found

    def test_get_with_type_hint_returns_none_or_default_for_missing_path(self):
        r = SlackResponse(ok=True)

        assert r.get("missing", type_=str) is None
        assert r.get("missing", default="fallback", type_=str) == "fallback"
        assert r.get("missing", "fallback", str) == "fallback"
        assert r.get("missing", default="fallback", type_=int) == "fallback"

    def test_get_overload_return_types(self):
        r = SlackResponse.model_validate({"ok": True, "count": "42"})

        assert assert_type(r.get("count", type_=int), int | None) == 42
        assert assert_type(r.get("count", 0, int), int) == 42
        assert (
            assert_type(r.get("missing", default="fallback", type_=int), int | str)
            == "fallback"
        )
        assert assert_type(r.get("missing", None, int), int | None) is None
        assert assert_type(r.get("count", default=0), Any) == "42"

    @pytest.mark.parametrize(
        ("value", "type_", "expected"),
        [
            ("42", int, 42),
            ("false", bool, False),
            ("hello", str, "hello"),
            (["1", "2"], list[int], [1, 2]),
        ],
    )
    def test_get_converts_and_validates_values(self, value, type_, expected):
        r = SlackResponse.model_validate({"ok": True, "value": value})

        result = r.get("value", type_=type_)

        assert result == expected
        assert type(result) is type(expected)
        assert r.get("value") == value
        assert r.try_get("value") == (True, value)

    def test_get_converts_nested_value_to_model(self):
        r = SlackResponse.model_validate(
            {"ok": True, "messages": [{"type": "message", "text": "hello"}]}
        )

        message = assert_type(
            r.get("messages[0]", type_=EventContent), EventContent | None
        )

        assert isinstance(message, EventContent)
        assert message.type == "message"
        assert message.text == "hello"

    def test_get_rejects_invalid_values_even_with_default(self):
        r = SlackResponse.model_validate({"ok": True, "message": {"text": "hello"}})

        with pytest.raises(ValidationError):
            r.get("message", type_=str)
        with pytest.raises(ValidationError):
            r.get("message.text", default=0, type_=int)
        with pytest.raises(ValidationError):
            r.get("message.text", type_=EventContent)

    def test_get_empty_path_validates_entire_model(self):
        r = SlackResponse(ok=True)

        assert r.get("") == r.model_dump(mode="json", by_alias=True)
        result = r.get("", type_=SlackResponse)
        assert isinstance(result, SlackResponse)
        assert result == r
        with pytest.raises(ValidationError):
            r.get("", type_=int)

    def test_get_existing_null_does_not_use_default(self):
        r = SlackResponse(ok=True, error=None)

        assert r.get("error", default="fallback") is None
        assert r.get("error", default="fallback", type_=type(None)) is None
        with pytest.raises(ValidationError):
            r.get("error", default="fallback", type_=str)
