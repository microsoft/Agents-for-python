import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from microsoft_agents.hosting.core.storage import FileTranscriptStore, PagedResult
from microsoft_agents.activity import Activity  # type: ignore


@pytest_asyncio.fixture
async def temp_logger():
    """Create a temporary logger with an isolated folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = FileTranscriptStore(tmpdir)
        yield logger


def make_activity(channel="testChannel", conv="conv1", text="hello") -> Activity:
    activity = Activity(
        id="activity1",
        type="message",
        channel_id=channel,
        conversation={"id": conv},
        text=text,
    )

    return activity


# ----------------------------
# log_activity
# ----------------------------


@pytest.mark.asyncio
async def test_log_activity_creates_file(temp_logger: FileTranscriptStore):
    activity = make_activity()
    await temp_logger.log_activity(activity)

    file_path = Path(temp_logger._root) / "testChannel" / "conv1.transcript"
    assert file_path.exists(), "Transcript file should be created"

    contents = file_path.read_text(encoding="utf-8").strip()
    assert contents, "Transcript file should not be empty"

    a = Activity.model_validate_json(contents)
    assert a.text == "hello"
    assert a.conversation.id == "conv1"


@pytest.mark.asyncio
async def test_log_activity_appends_multiple_lines(temp_logger: FileTranscriptStore):
    activity1 = make_activity(text="first")
    activity2 = make_activity(text="second")
    await temp_logger.log_activity(activity1)
    await temp_logger.log_activity(activity2)

    file_path = Path(temp_logger._root) / "testChannel" / "conv1.transcript"
    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    texts = [json.loads(l)["text"] for l in lines]
    assert texts == ["first", "second"]


# ----------------------------
# list_transcripts
# ----------------------------


@pytest.mark.asyncio
async def test_list_transcripts_returns_conversations(temp_logger: FileTranscriptStore):
    await temp_logger.log_activity(make_activity(conv="convA"))
    await temp_logger.log_activity(make_activity(conv="convB"))
    result = await temp_logger.list_transcripts("testChannel")

    assert isinstance(result, PagedResult)
    ids = [t.conversation_id for t in result.items]
    assert {"convA", "convB"} <= set(ids)


@pytest.mark.asyncio
async def test_list_transcripts_empty_channel(temp_logger: FileTranscriptStore):
    result = await temp_logger.list_transcripts("nonexistent")
    assert isinstance(result, PagedResult)
    assert result.items == []


# ----------------------------
# get_transcript_activities
# ----------------------------


@pytest.mark.asyncio
async def test_get_transcript_activities_reads_logged_items(
    temp_logger: FileTranscriptStore,
):
    for i in range(3):
        await temp_logger.log_activity(make_activity(conv="convX", text=f"msg{i}"))

    result = await temp_logger.get_transcript_activities("testChannel", "convX")
    texts = [a.text for a in result.items]
    assert texts == ["msg0", "msg1", "msg2"]
    assert result.continuation_token is None


@pytest.mark.asyncio
async def test_get_transcript_activities_with_paging(temp_logger: FileTranscriptStore):
    # Add many lines to force paging
    for i in range(50):
        await temp_logger.log_activity(make_activity(conv="paged", text=f"msg{i}"))

    first = await temp_logger.get_transcript_activities(
        "testChannel", "paged", page_bytes=300
    )
    assert len(first.items) > 0
    assert first.continuation_token is not None

    second = await temp_logger.get_transcript_activities(
        "testChannel",
        "paged",
        continuation_token=first.continuation_token,
        page_bytes=300,
    )
    assert len(second.items) > 0
    assert all("msg" in a.text for a in second.items)


@pytest.mark.asyncio
async def test_get_transcript_activities_with_start_date_filter(
    temp_logger: FileTranscriptStore,
):
    old_ts = datetime.now(timezone.utc) - timedelta(days=2)
    new_ts = datetime.now(timezone.utc)

    activity1 = make_activity(conv="filtered", text="old")
    activity2 = make_activity(conv="filtered", text="new")
    activity1.timestamp = old_ts
    activity2.timestamp = new_ts

    await temp_logger.log_activity(activity1)
    await temp_logger.log_activity(activity2)

    start_date = datetime.now(timezone.utc) - timedelta(days=1)
    result = await temp_logger.get_transcript_activities(
        "testChannel", "filtered", start_date=start_date
    )
    texts = [a.text for a in result.items]
    assert texts == ["new"]


# ----------------------------
# delete_transcript
# ----------------------------


@pytest.mark.asyncio
async def test_delete_transcript_removes_file(temp_logger: FileTranscriptStore):
    await temp_logger.log_activity(make_activity(conv="todelete"))
    file_path = Path(temp_logger._root) / "testChannel" / "todelete.transcript"
    assert file_path.exists()

    await temp_logger.delete_transcript("testChannel", "todelete")
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_delete_transcript_nonexistent(temp_logger: FileTranscriptStore):
    # Should not raise any errors
    await temp_logger.delete_transcript("channel", "nonexistent")
