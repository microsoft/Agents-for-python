# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import urllib.parse

from asyncio import Lock
from typing import overload

from a2a.server.context import ServerCallContext
from a2a.server.tasks import TaskStore
from a2a.types.a2a_pb2 import (
    ListTasksRequest,
    ListTasksResponse,
    Task,
    TaskState,
)


from azure.storage.blob.aio import (
    ContainerClient,
    BlobServiceClient,
)
from microsoft_agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)

_TASK_PREFIX = "TODO"


class BlobTaskStore(TaskStore):
    """A task store implementation backed by a blob storage."""

    @overload
    def __init__(
        self,
        container_client: ContainerClient,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        data_connection_string: str,
        container_name: str,
    ) -> None: ...
    def __init__(
        self,
        container_client: ContainerClient | None = None,
        *,
        data_connection_string: str | None = None,
        container_name: str | None = None,
    ) -> None:
        """Initializes the blob task store with either a container client or a connection string and container name.

        :param container_client: An optional ContainerClient instance for accessing the blob storage.
        :param data_connection_string: An optional connection string for the blob storage.
        :param container_name: An optional container name within the blob storage.
        """

        self._initialized = False
        self._init_lock = Lock()

        if container_client is not None:
            self._container_client = container_client
            return
        elif data_connection_string is not None and container_name is not None:
            blob_service_client = BlobServiceClient.from_connection_string(
                data_connection_string
            )
            self._container_client = blob_service_client.get_container_client(
                container_name
            )
            return
        else:
            raise ValueError("Invalid combination of parameters provided.")

    async def _ensure_container_exists(self) -> None:
        """Ensures that the blob container exists, creating it if necessary."""

        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:
                    await ignore_error(
                        self._container_client.create_container(),
                        is_status_code_error(409),
                    )
                    self._initialized = True

    @staticmethod
    def _should_include_task(task: Task, request: ListTasksRequest) -> bool:
        """Determines whether a task should be included in the list based on the request parameters."""

        if (
            request.status != TaskState.TASK_STATE_UNSPECIFIED
            and request.status != task.status.state
        ):
            return False
        if request.context_id and request.context_id != task.context_id:
            return False
        return True

    @staticmethod
    def _get_blob_name(task_id: str) -> str:
        """Generates a blob name for the given task ID."""

        if not task_id:
            raise ValueError("Task ID cannot be empty.")
        return f"{_TASK_PREFIX}{urllib.parse.quote_plus(task_id)}"

    async def save(self, task: Task, context: ServerCallContext) -> None:
        """Saves or updates a task in the blob store."""
        await self._ensure_container_exists()

        blob_name = self._get_blob_name(task.id)
        blob_client = self._container_client.get_blob_client(blob_name)
        serialized_task = task.SerializeToString()

        await blob_client.upload_blob(
            data=serialized_task,
            overwrite=True,
            length=len(serialized_task),
        )

    async def get(self, task_id: str, context: ServerCallContext) -> Task | None:
        """Retrieves a task from the blob store by its ID.

        :param task_id: The ID of the task to retrieve.
        :param context: The server call context.
        :return: The task if found, otherwise None.
        """
        await self._ensure_container_exists()

        return await self._download_task(task_id)

    async def list(
        self, params: ListTasksRequest, context: ServerCallContext
    ) -> ListTasksResponse:
        """Retrives a list of tasks from the store.

        :param params: The parameters for listing tasks.
        :param context: The server call context.
        :return: A response containing the list of tasks.
        """
        await self._ensure_container_exists()

        tasks: list[Task] = []

        items = self._container_client.list_blobs(
            name_starts_with=_TASK_PREFIX, results_per_page=params.page_size
        )

        iterator = items.by_page(params.page_token)
        first_page = await anext(iterator)

        if not first_page:
            return ListTasksResponse(tasks=[], next_page_token=None)

        next_page_token = getattr(first_page, "continuation_token", None)

        # TODO ->
        async for blob in first_page:
            task = await self._download_task_blob(blob.name)
            if task and self._should_include_task(task, params):
                tasks.append(task)

        return ListTasksResponse(tasks=tasks, next_page_token=next_page_token)

    async def delete(self, task_id: str, context: ServerCallContext) -> None:
        """Deletes a task from the blob store by its ID.

        :param task_id: The ID of the task to delete.
        :param context: The server call context.s
        """
        await self._ensure_container_exists()

        blob_name = self._get_blob_name(task_id)
        await self._container_client.get_blob_client(blob_name).delete_blob()

    async def _download_task(self, task_id: str) -> Task | None:
        return await self._download_task_blob(self._get_blob_name(task_id))

    async def _download_task_blob(self, blob_name: str) -> Task | None:
        item = await ignore_error(
            self._container_client.download_blob(blob=blob_name, timeout=5),
            is_status_code_error(404),
        )
        if not item:
            return None

        serialized_task: bytes = await item.readall()
        task = Task()
        task.ParseFromString(serialized_task)

        return task
