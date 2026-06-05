"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from microsoft_agents.hosting.slack.api import SlackResponse


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
