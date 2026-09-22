# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a.types import Task, TaskState, TaskStatus
from google.protobuf.message import DecodeError

from microsoft_agents.hosting.a2a.blob_task_store import BlobTaskStore


def _task(task_id: str = "task/1") -> Task:
    return Task(
        id=task_id,
        context_id="context-1",
        status=TaskStatus(
            state=TaskState.TASK_STATE_WORKING,
        ),
    )


def _store():
    container_client = MagicMock()
    container_client.create_container = AsyncMock()
    store = BlobTaskStore(container_client)
    store._initialized = True
    return store, container_client


@pytest.mark.asyncio
async def test_save_uploads_serialized_protobuf():
    store, container_client = _store()
    blob_client = MagicMock()
    blob_client.upload_blob = AsyncMock()
    container_client.get_blob_client.return_value = blob_client
    task = _task()

    await store.save(task, context=MagicMock())

    container_client.get_blob_client.assert_called_once_with("TODOtask%2F1")
    blob_client.upload_blob.assert_awaited_once_with(
        data=task.SerializeToString(),
        overwrite=True,
        length=len(task.SerializeToString()),
    )


@pytest.mark.asyncio
async def test_get_deserializes_protobuf_task():
    store, container_client = _store()
    task = _task()
    downloader = SimpleNamespace(readall=AsyncMock(return_value=task.SerializeToString()))
    container_client.download_blob = AsyncMock(return_value=downloader)

    result = await store.get(task.id, context=MagicMock())

    assert result == task
    assert result is not task
    container_client.download_blob.assert_awaited_once_with(
        blob="TODOtask%2F1",
        timeout=5,
    )


@pytest.mark.asyncio
async def test_download_task_blob_uses_existing_blob_name():
    store, container_client = _store()
    task = _task()
    downloader = SimpleNamespace(readall=AsyncMock(return_value=task.SerializeToString()))
    container_client.download_blob = AsyncMock(return_value=downloader)

    result = await store._download_task_blob("TODOtask%2F1")

    assert result == task
    container_client.download_blob.assert_awaited_once_with(
        blob="TODOtask%2F1",
        timeout=5,
    )


@pytest.mark.asyncio
async def test_get_returns_none_when_blob_does_not_exist():
    store, container_client = _store()
    container_client.download_blob = AsyncMock(return_value=None)

    assert await store.get("missing", context=MagicMock()) is None


@pytest.mark.asyncio
async def test_get_propagates_invalid_protobuf_data():
    store, container_client = _store()
    downloader = SimpleNamespace(readall=AsyncMock(return_value=b"not protobuf"))
    container_client.download_blob = AsyncMock(return_value=downloader)

    with pytest.raises(DecodeError):
        await store.get("invalid", context=MagicMock())
