# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import pytest
from a2a.server.context import ServerCallContext
from a2a.types import ListTasksRequest, Task, TaskState, TaskStatus
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from dotenv import load_dotenv
from google.protobuf.message import DecodeError

from microsoft_agents.hosting.a2a.blob_task_store import BlobTaskStore

# To enable these tests, run with --run-blob and configure either:
# TEST_BLOB_STORAGE_CONNECTION_STRING or TEST_BLOB_STORAGE_ACCOUNT_URL.


def _task(
    task_id: str,
    *,
    context_id: str = "context-1",
    state: TaskState = TaskState.TASK_STATE_WORKING,
) -> Task:
    return Task(
        id=task_id,
        context_id=context_id,
        status=TaskStatus(state=state),
    )


@asynccontextmanager
async def _blob_task_store():
    load_dotenv()
    connection_string = os.environ.get("TEST_BLOB_STORAGE_CONNECTION_STRING")
    credential = None

    if connection_string:
        service_client = BlobServiceClient.from_connection_string(connection_string)
    else:
        account_url = os.environ.get("TEST_BLOB_STORAGE_ACCOUNT_URL")
        if not account_url:
            pytest.skip(
                "Set TEST_BLOB_STORAGE_CONNECTION_STRING or "
                "TEST_BLOB_STORAGE_ACCOUNT_URL"
            )
        credential = DefaultAzureCredential()
        service_client = BlobServiceClient(account_url, credential=credential)

    container_name = f"asdka2atasks{uuid.uuid4().hex}"
    container_client = service_client.get_container_client(container_name)
    store = BlobTaskStore(container_client)

    try:
        yield store, container_client
    finally:
        try:
            await container_client.delete_container()
        except ResourceNotFoundError:
            pass
        await container_client.close()
        await service_client.close()
        if credential:
            await credential.close()


async def _upload_blob(container_client: ContainerClient, name: str, data: bytes):
    blob_client = await container_client.upload_blob(
        name=name,
        data=data,
        overwrite=True,
    )
    await blob_client.close()


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


@pytest.mark.blob
class TestBlobTaskStore:
    @pytest.mark.asyncio
    async def test_save_get_and_overwrite_task(self):
        context = ServerCallContext()

        async with _blob_task_store() as (store, container_client):
            task = _task("task/with spaces")

            await store.save(task, context)

            saved = await store.get(task.id, context)
            assert saved == task
            assert saved is not task

            blob_names = [blob.name async for blob in container_client.list_blobs()]
            assert blob_names == ["TODOtask%2Fwith+spaces"]

            task.status.state = TaskState.TASK_STATE_COMPLETED
            await store.save(task, context)

            overwritten = await store.get(task.id, context)
            assert overwritten == task
            assert overwritten.status.state == TaskState.TASK_STATE_COMPLETED

    @pytest.mark.asyncio
    async def test_external_blob_change_is_visible(self):
        context = ServerCallContext()
        external_task = _task("external-task")

        async with _blob_task_store() as (store, container_client):
            assert await store.get(external_task.id, context) is None

            await _upload_blob(
                container_client,
                "TODOexternal-task",
                external_task.SerializeToString(),
            )

            assert await store.get(external_task.id, context) == external_task

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_task(self):
        async with _blob_task_store() as (store, _):
            assert await store.get("missing-task", ServerCallContext()) is None

    @pytest.mark.asyncio
    async def test_get_rejects_corrupted_task_blob(self):
        context = ServerCallContext()

        async with _blob_task_store() as (store, container_client):
            assert await store.get("corrupted-task", context) is None
            await _upload_blob(
                container_client,
                "TODOcorrupted-task",
                b"not a serialized Task",
            )

            with pytest.raises(DecodeError):
                await store.get("corrupted-task", context)

    @pytest.mark.asyncio
    async def test_list_filters_by_status_and_context(self):
        context = ServerCallContext()
        matching = _task("task-1")
        tasks = [
            matching,
            _task("task-2", context_id="other-context"),
            _task("task-3", state=TaskState.TASK_STATE_COMPLETED),
        ]

        async with _blob_task_store() as (store, _):
            await asyncio.gather(*(store.save(task, context) for task in tasks))

            response = await store.list(
                ListTasksRequest(
                    status=TaskState.TASK_STATE_WORKING,
                    context_id="context-1",
                ),
                context,
            )

            assert list(response.tasks) == [matching]
            assert response.next_page_token == ""

    @pytest.mark.asyncio
    async def test_list_uses_azure_continuation_tokens(self):
        context = ServerCallContext()
        tasks = [_task(f"task-{index}") for index in range(3)]

        async with _blob_task_store() as (store, _):
            await asyncio.gather(*(store.save(task, context) for task in tasks))

            first_page = await store.list(
                ListTasksRequest(page_size=2),
                context,
            )
            second_page = await store.list(
                ListTasksRequest(
                    page_size=2,
                    page_token=first_page.next_page_token,
                ),
                context,
            )

            assert [task.id for task in first_page.tasks] == [
                "task-0",
                "task-1",
            ]
            assert first_page.next_page_token
            assert [task.id for task in second_page.tasks] == ["task-2"]
            assert second_page.next_page_token == ""

    @pytest.mark.asyncio
    async def test_concurrent_first_operations_share_container_initialization(self):
        context = ServerCallContext()
        tasks = [_task(f"task-{index}") for index in range(3)]

        async with _blob_task_store() as (store, _):
            await asyncio.gather(*(store.save(task, context) for task in tasks))
            saved = await asyncio.gather(
                *(store.get(task.id, context) for task in tasks)
            )

            assert saved == tasks

    @pytest.mark.asyncio
    async def test_delete_removes_persisted_task(self):
        context = ServerCallContext()
        task = _task("task/to-delete")

        async with _blob_task_store() as (store, _):
            await store.save(task, context)
            assert await store.get(task.id, context) == task

            await store.delete(task.id, context)

            assert await store.get(task.id, context) is None
