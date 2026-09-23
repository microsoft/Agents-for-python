# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from a2a.types import ListTasksRequest, Task, TaskState, TaskStatus
from google.protobuf.message import DecodeError

from microsoft_agents.hosting.a2a.blob_task_store import BlobTaskStore

blob_task_store_module = importlib.import_module(
    "microsoft_agents.hosting.a2a.blob_task_store"
)


class _AsyncIterator:
    def __init__(self, values):
        self._values = iter(values)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._values)
        except StopIteration as error:
            raise StopAsyncIteration from error


class _BlobPage:
    def __init__(self, blob_names, continuation_token=None):
        self._blobs = [SimpleNamespace(name=blob_name) for blob_name in blob_names]
        self.continuation_token = continuation_token

    def __aiter__(self):
        return _AsyncIterator(self._blobs)


def _task(
    task_id: str = "task/1",
    *,
    context_id: str = "context-1",
    state: TaskState = TaskState.TASK_STATE_WORKING,
) -> Task:
    return Task(
        id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=state,
        ),
    )


def _store():
    container_client = MagicMock()
    container_client.create_container = AsyncMock()
    store = BlobTaskStore(container_client)
    store._initialized = True
    return store, container_client


def test_constructor_uses_provided_container_client():
    container_client = MagicMock()

    store = BlobTaskStore(container_client)

    assert store._container_client is container_client
    assert store._initialized is False


def test_constructor_creates_container_client_from_connection_string():
    blob_service_client = MagicMock()
    container_client = MagicMock()
    blob_service_client.get_container_client.return_value = container_client

    with patch.object(
        blob_task_store_module.BlobServiceClient,
        "from_connection_string",
        return_value=blob_service_client,
    ) as from_connection_string:
        store = BlobTaskStore(
            data_connection_string="UseDevelopmentStorage=true",
            container_name="tasks",
        )

    from_connection_string.assert_called_once_with("UseDevelopmentStorage=true")
    blob_service_client.get_container_client.assert_called_once_with("tasks")
    assert store._container_client is container_client


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"data_connection_string": "connection"},
        {"container_name": "tasks"},
    ],
)
def test_constructor_rejects_invalid_parameter_combinations(kwargs):
    with pytest.raises(ValueError, match="Invalid combination"):
        BlobTaskStore(**kwargs)


@pytest.mark.asyncio
async def test_ensure_container_exists_initializes_only_once():
    container_client = MagicMock()
    container_client.create_container = AsyncMock()
    store = BlobTaskStore(container_client)

    await asyncio.gather(
        store._ensure_container_exists(),
        store._ensure_container_exists(),
        store._ensure_container_exists(),
    )

    container_client.create_container.assert_awaited_once()
    assert store._initialized is True


@pytest.mark.parametrize(
    ("task_id", "expected"),
    [
        ("task-1", "TODOtask-1"),
        ("task/1", "TODOtask%2F1"),
        ("task with spaces", "TODOtask+with+spaces"),
        ("task+plus", "TODOtask%2Bplus"),
    ],
)
def test_get_blob_name_encodes_task_id(task_id, expected):
    assert BlobTaskStore._get_blob_name(task_id) == expected


def test_get_blob_name_rejects_empty_task_id():
    with pytest.raises(ValueError, match="Task ID cannot be empty"):
        BlobTaskStore._get_blob_name("")


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
async def test_save_initializes_container_before_upload():
    container_client = MagicMock()
    container_client.create_container = AsyncMock()
    blob_client = MagicMock()
    blob_client.upload_blob = AsyncMock()
    container_client.get_blob_client.return_value = blob_client
    store = BlobTaskStore(container_client)

    await store.save(_task(), context=MagicMock())

    container_client.create_container.assert_awaited_once()
    blob_client.upload_blob.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_deserializes_protobuf_task():
    store, container_client = _store()
    task = _task()
    downloader = SimpleNamespace(
        readall=AsyncMock(return_value=task.SerializeToString())
    )
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
    downloader = SimpleNamespace(
        readall=AsyncMock(return_value=task.SerializeToString())
    )
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


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (ListTasksRequest(), True),
        (
            ListTasksRequest(status=TaskState.TASK_STATE_WORKING),
            True,
        ),
        (
            ListTasksRequest(status=TaskState.TASK_STATE_COMPLETED),
            False,
        ),
        (
            ListTasksRequest(context_id="context-1"),
            True,
        ),
        (
            ListTasksRequest(context_id="other-context"),
            False,
        ),
    ],
)
def test_should_include_task_filters_by_status_and_context(params, expected):
    assert BlobTaskStore._should_include_task(_task(), params) is expected


@pytest.mark.asyncio
async def test_list_returns_filtered_tasks_and_continuation_token():
    store, container_client = _store()
    page = _BlobPage(
        ["TODOtask-1", "TODOtask-2", "TODOmissing"],
        continuation_token="next-page",
    )
    items = MagicMock()
    items.by_page.return_value = _AsyncIterator([page])
    container_client.list_blobs.return_value = items
    matching_task = _task("task-1")
    other_context_task = _task("task-2", context_id="other-context")
    store._download_task_blob = AsyncMock(
        side_effect=[matching_task, other_context_task, None]
    )
    params = ListTasksRequest(
        status=TaskState.TASK_STATE_WORKING,
        context_id="context-1",
        page_size=25,
        page_token="current-page",
    )

    response = await store.list(params, context=MagicMock())

    container_client.list_blobs.assert_called_once_with(
        name_starts_with="TODO",
        results_per_page=25,
    )
    items.by_page.assert_called_once_with("current-page")
    assert list(response.tasks) == [matching_task]
    assert response.next_page_token == "next-page"
    assert store._download_task_blob.await_count == 3


@pytest.mark.asyncio
async def test_list_returns_empty_response_for_empty_page():
    store, container_client = _store()
    page = _BlobPage([])
    items = MagicMock()
    items.by_page.return_value = _AsyncIterator([page])
    container_client.list_blobs.return_value = items

    response = await store.list(ListTasksRequest(), context=MagicMock())

    assert list(response.tasks) == []
    assert response.next_page_token == ""


@pytest.mark.asyncio
async def test_delete_deletes_encoded_blob_name():
    store, container_client = _store()
    blob_client = MagicMock()
    blob_client.delete_blob = AsyncMock()
    container_client.get_blob_client.return_value = blob_client

    await store.delete("task/1", context=MagicMock())

    container_client.get_blob_client.assert_called_once_with("TODOtask%2F1")
    blob_client.delete_blob.assert_awaited_once()
