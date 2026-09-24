# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import httpx
import pytest
from a2a.types import (
    AgentInterface,
    ListTasksRequest,
    Message,
    Part,
    Role,
    SendMessageRequest,
)
from a2a.utils.constants import TransportProtocol
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from dotenv import load_dotenv
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict

from microsoft_agents.hosting.a2a import A2AAdapter, add_a2a
from microsoft_agents.hosting.a2a.blob_task_store import BlobTaskStore

from .conftest import _create_agent_application

pytestmark = [
    pytest.mark.blob,
    pytest.mark.integration,
    pytest.mark.filterwarnings(
        "ignore:label\\(\\) is deprecated\\. Use is_required\\(\\) or is_repeated\\(\\) instead\\.:DeprecationWarning"
    ),
]


def _send_request(text: str) -> SendMessageRequest:
    return SendMessageRequest(
        message=Message(
            role=Role.ROLE_USER,
            message_id=str(uuid.uuid4()),
            parts=[Part(text=text)],
        )
    )


def _rpc_request(method: str, params: object, request_id: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": MessageToDict(params),
    }


async def _post_rpc(
    client: httpx.AsyncClient,
    method: str,
    params: object,
    request_id: str,
) -> dict:
    response = await client.post(
        "/rpc",
        json=_rpc_request(method, params, request_id),
        headers={"A2A-Version": "1.0"},
    )
    assert response.status_code == 200
    return response.json()


@asynccontextmanager
async def _blob_container():
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

    container_name = f"asdka2aprotocol{uuid.uuid4().hex}"
    container_client = service_client.get_container_client(container_name)

    try:
        yield container_client
    finally:
        try:
            await container_client.delete_container()
        except ResourceNotFoundError:
            pass
        await container_client.close()
        await service_client.close()
        if credential:
            await credential.close()


@asynccontextmanager
async def _blob_backed_a2a_client(container_client: ContainerClient):
    app = FastAPI()
    agent = _create_agent_application(asyncio.Event(), asyncio.Event())
    adapter = A2AAdapter(
        agent,
        agent_interfaces=[
            AgentInterface(
                url="/rpc",
                protocol_binding=TransportProtocol.JSONRPC,
            ),
            AgentInterface(
                url="/rest",
                protocol_binding=TransportProtocol.HTTP_JSON,
            ),
        ],
        task_store=BlobTaskStore(container_client),
    )
    add_a2a(app, agent, adapter=adapter, use_jwt_middleware=False)

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        await adapter.a2a_request_handler.aclose()


@pytest.mark.asyncio
async def test_task_persists_across_app_restart_and_protocols():
    async with _blob_container() as container_client:
        async with _blob_backed_a2a_client(container_client) as client:
            sent = await _post_rpc(
                client,
                "SendMessage",
                _send_request("persisted"),
                "send-task",
            )
            task = sent["result"]["task"]

        async with _blob_backed_a2a_client(container_client) as restarted_client:
            get_response = await restarted_client.get(
                f"/rest/tasks/{task['id']}",
                headers={"A2A-Version": "1.0"},
            )
            list_response = await restarted_client.get(
                "/rest/tasks",
                headers={"A2A-Version": "1.0"},
            )

        assert get_response.status_code == 200
        assert get_response.json() == task
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()["tasks"]] == [task["id"]]


@pytest.mark.asyncio
async def test_jsonrpc_list_tasks_uses_blob_continuation_tokens():
    async with _blob_container() as container_client:
        async with _blob_backed_a2a_client(container_client) as client:
            task_ids = set()
            for index in range(3):
                sent = await _post_rpc(
                    client,
                    "SendMessage",
                    _send_request(f"task-{index}"),
                    f"send-{index}",
                )
                task_ids.add(sent["result"]["task"]["id"])

            first_page = await _post_rpc(
                client,
                "ListTasks",
                ListTasksRequest(page_size=2),
                "list-first-page",
            )
            first_result = first_page["result"]
            second_page = await _post_rpc(
                client,
                "ListTasks",
                ListTasksRequest(
                    page_size=2,
                    page_token=first_result["nextPageToken"],
                ),
                "list-second-page",
            )
            second_result = second_page["result"]

        first_ids = {task["id"] for task in first_result["tasks"]}
        second_ids = {task["id"] for task in second_result["tasks"]}

        assert len(first_ids) == 2
        assert first_result["nextPageToken"]
        assert len(second_ids) == 1
        assert second_result.get("nextPageToken", "") == ""
        assert first_ids.isdisjoint(second_ids)
        assert first_ids | second_ids == task_ids
