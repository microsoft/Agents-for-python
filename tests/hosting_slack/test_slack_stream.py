"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from microsoft_agents.hosting.slack.api import (
    BlocksChunk,
    MarkdownTextChunk,
    SlackResponse,
    SlackStream,
    SlackTaskStatus,
    TaskUpdateChunk,
)


def _fake_api(start_ts: str = "1.0"):
    api = MagicMock()
    api.call = AsyncMock(return_value=SlackResponse(ok=True, ts=start_ts))
    return api


@pytest.mark.asyncio
async def test_start_records_ts_and_calls_chat_startStream():
    api = _fake_api(start_ts="100.0")
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    method, body, token = api.call.call_args.args
    assert method == "chat.startStream"
    assert token == "tok"
    assert body == {
        "channel": "C1",
        "thread_ts": "thread1",
        "task_display_mode": "plan",
    }


@pytest.mark.asyncio
async def test_append_string_wraps_in_markdown_chunk():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    await stream.append("hello world")
    method, body, _ = api.call.call_args.args
    assert method == "chat.appendStream"
    assert body["chunks"] == [{"type": "markdown_text", "text": "hello world"}]


@pytest.mark.asyncio
async def test_append_chunk_list():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    await stream.append(
        [
            MarkdownTextChunk(text="hi "),
            TaskUpdateChunk(
                id="t1", title="Doing it", status=SlackTaskStatus.IN_PROGRESS
            ),
        ]
    )
    body = api.call.call_args.args[1]
    assert body["chunks"][0]["type"] == "markdown_text"
    assert body["chunks"][1]["type"] == "task_update"
    assert body["chunks"][1]["id"] == "t1"
    assert body["chunks"][1]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_append_empty_list_no_call():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    await stream.append([])
    api.call.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_with_blocks_string_object_extracts_array():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    blocks_json = '{"blocks": [{"type": "section"}]}'
    await stream.stop(blocks=blocks_json)
    method, body, _ = api.call.call_args.args
    assert method == "chat.stopStream"
    assert body["blocks"] == [{"type": "section"}]


@pytest.mark.asyncio
async def test_stop_with_blocks_array_string_passes_through():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    await stream.stop(blocks='[{"type": "section"}]')
    body = api.call.call_args.args[1]
    assert body["blocks"] == [{"type": "section"}]


@pytest.mark.asyncio
async def test_stop_with_object_missing_blocks_array_raises():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()

    with pytest.raises(ValueError):
        await stream.stop(blocks='{"foo": "bar"}')


@pytest.mark.asyncio
async def test_stop_before_start_is_noop():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.stop()
    api.call.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_with_python_blocks_list():
    api = _fake_api()
    stream = SlackStream(api, "C1", "thread1", "tok")
    await stream.start()
    api.call.reset_mock()

    await stream.stop(
        chunks=[MarkdownTextChunk(text="done")],
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "ok"}}],
    )
    body = api.call.call_args.args[1]
    assert body["blocks"][0]["type"] == "section"
    assert body["chunks"][0]["text"] == "done"
