# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import uuid

import httpx
import pytest
from google.protobuf.json_format import MessageToDict

from a2a.types.a2a_pb2 import (
    CancelTaskRequest,
    GetTaskRequest,
    ListTasksRequest,
    Message,
    Part,
    Role,
    SendMessageRequest,
)

pytestmark = pytest.mark.filterwarnings(
    "ignore:label\\(\\) is deprecated\\. Use is_required\\(\\) or is_repeated\\(\\) instead\\.:DeprecationWarning"
)


def _message(text: str = "hello") -> Message:
    return Message(
        role=Role.ROLE_USER,
        message_id=str(uuid.uuid4()),
        parts=[Part(text=text)],
    )


def _send_request(text: str = "hello") -> SendMessageRequest:
    return SendMessageRequest(message=_message(text))


def _rpc_request(method: str, params: object, request_id: str = "request-1") -> dict:
    serialized_params = (
        MessageToDict(params) if hasattr(params, "DESCRIPTOR") else params
    )
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": serialized_params,
    }


async def _post_rpc(
    client: httpx.AsyncClient,
    method: str,
    params: object,
    request_id: str = "request-1",
) -> dict:
    response = await client.post(
        "/rpc",
        json=_rpc_request(method, params, request_id),
        headers={"A2A-Version": "1.0"},
    )
    assert response.status_code == 200
    return response.json()


def _task_id(response: dict) -> str:
    return response["result"]["task"]["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_card_describes_configured_interfaces_and_skill(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await a2a_client.get("/rpc/.well-known/agent-card.json")

    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "Compatibility Agent"
    assert card["version"] == "1.0.0"
    assert {item["url"] for item in card["supportedInterfaces"]} == {
        "http://testserver/rpc",
        "http://testserver/rest",
    }
    assert card["skills"][0]["id"] == "echo"
    assert card["capabilities"]["streaming"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_message_send_get_and_list(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await _post_rpc(
        a2a_client,
        "SendMessage",
        _send_request("json-rpc"),
    )

    assert response["result"]["task"]["status"]["state"] == "TASK_STATE_COMPLETED"
    task_id = _task_id(response)
    context_id = response["result"]["task"]["contextId"]
    assert response["result"]["task"]["history"][1]["parts"][0]["text"] == (
        "Echo: json-rpc"
    )

    get_response = await _post_rpc(
        a2a_client,
        "GetTask",
        GetTaskRequest(id=task_id),
        request_id="get-task",
    )
    assert get_response["result"]["id"] == task_id
    assert get_response["result"]["contextId"] == context_id

    list_response = await _post_rpc(
        a2a_client,
        "ListTasks",
        ListTasksRequest(context_id=context_id),
        request_id="list-tasks",
    )
    assert [task["id"] for task in list_response["result"]["tasks"]] == [task_id]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_message_send_get_and_list_match_jsonrpc_semantics(
    a2a_client: httpx.AsyncClient,
) -> None:
    request = _send_request("rest")
    response = await a2a_client.post(
        "/rest/message:send",
        json=MessageToDict(request),
        headers={"A2A-Version": "1.0"},
    )

    assert response.status_code == 200
    task = response.json()["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    task_id = task["id"]

    get_response = await a2a_client.get(
        f"/rest/tasks/{task_id}",
        headers={"A2A-Version": "1.0"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    list_response = await a2a_client.get(
        "/rest/tasks",
        headers={"A2A-Version": "1.0"},
    )
    assert list_response.status_code == 200
    assert any(item["id"] == task_id for item in list_response.json()["tasks"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_cancel_missing_task_returns_protocol_error(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await _post_rpc(
        a2a_client,
        "CancelTask",
        CancelTaskRequest(id="missing-task"),
        request_id="cancel-task",
    )

    assert response["id"] == "cancel-task"
    assert response["error"]["code"] != 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_rejects_unknown_method(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await a2a_client.post(
        "/rpc",
        json=_rpc_request("UnsupportedMethod", {}, request_id="unknown"),
        headers={"A2A-Version": "1.0"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "unknown"
    assert payload["error"]["code"] == -32601
