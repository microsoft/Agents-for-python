"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

import pytest

from microsoft_agents.hosting.slack.api import (
    SlackApi,
    SlackResponseException,
)


class _FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.ok = 200 <= status < 300
        self._body = body

    async def text(self) -> str:
        return self._body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *_args: Any) -> None:
        return None


class _FakeSession:
    """Records each POST call and returns a pre-canned response."""

    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, *, data: str, headers: dict, timeout=None):
        self.calls.append(
            {"url": url, "data": data, "headers": dict(headers), "timeout": timeout}
        )
        return self._response

    async def close(self) -> None:  # honoured if owned
        return None


@pytest.mark.asyncio
async def test_call_serializes_dict_and_sends_bearer_token():
    session = _FakeSession(_FakeResponse(200, '{"ok": true, "ts": "123.456"}'))
    api = SlackApi(session=session)

    result = await api.call(
        "chat.postMessage",
        {"channel": "C1", "text": "hi", "drop_me": None},
        token="xoxb-abc",
    )

    assert result.ok is True
    assert result.ts == "123.456"
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "https://slack.com/api/chat.postMessage"
    assert call["headers"]["Authorization"] == "Bearer xoxb-abc"
    body = json.loads(call["data"])
    # None values are stripped before serialization
    assert body == {"channel": "C1", "text": "hi"}


@pytest.mark.asyncio
async def test_call_uses_string_body_verbatim():
    session = _FakeSession(_FakeResponse(200, '{"ok": true}'))
    api = SlackApi(session=session)
    raw = '{"channel":"C1","text":"raw"}'

    await api.call("chat.postMessage", raw, token="t")

    assert session.calls[0]["data"] == raw


@pytest.mark.asyncio
async def test_call_without_token_omits_authorization_header():
    session = _FakeSession(_FakeResponse(200, '{"ok": true}'))
    api = SlackApi(session=session)
    await api.call("auth.test")
    assert "Authorization" not in session.calls[0]["headers"]


@pytest.mark.asyncio
async def test_call_raises_on_non_ok_response():
    session = _FakeSession(
        _FakeResponse(200, '{"ok": false, "error": "channel_not_found"}')
    )
    api = SlackApi(session=session)

    with pytest.raises(SlackResponseException) as exc_info:
        await api.call("chat.postMessage", {"channel": "X"}, token="t")
    assert "channel_not_found" in str(exc_info.value) or "ok" in str(exc_info.value)
    # The exception carries the parsed response
    assert exc_info.value.response is not None
    assert exc_info.value.response.error == "channel_not_found"


@pytest.mark.asyncio
async def test_call_raises_on_http_error_with_unparseable_body():
    session = _FakeSession(_FakeResponse(500, "<html>oops</html>"))
    api = SlackApi(session=session)
    with pytest.raises(SlackResponseException):
        await api.call("chat.postMessage", {}, token="t")


@pytest.mark.asyncio
async def test_call_rejects_blank_method():
    api = SlackApi(session=_FakeSession(_FakeResponse(200, '{"ok": true}')))
    with pytest.raises(ValueError):
        await api.call("   ")


@pytest.mark.asyncio
async def test_pydantic_model_options_are_dumped_without_nulls():
    from pydantic import BaseModel

    class Opts(BaseModel):
        channel: str
        text: str | None = None

    session = _FakeSession(_FakeResponse(200, '{"ok": true}'))
    api = SlackApi(session=session)
    await api.call("chat.postMessage", Opts(channel="C1"), token="t")
    body = json.loads(session.calls[0]["data"])
    assert body == {"channel": "C1"}
