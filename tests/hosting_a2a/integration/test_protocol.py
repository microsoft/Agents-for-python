# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
import base64
import json
import uuid

import httpx
import pytest
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Value

from a2a.types.a2a_pb2 import (
    CancelTaskRequest,
    GetExtendedAgentCardRequest,
    GetTaskRequest,
    ListTasksRequest,
    Message,
    Part,
    Role,
    SendMessageRequest,
    SubscribeToTaskRequest,
)

from .conftest import (
    A2ATestHarness,
    FAILURE_TRIGGER_TEXT,
    INPUT_REQUIRED_TRIGGER_TEXT,
    LONG_RUNNING_TRIGGER_TEXT,
    PARTS_TRIGGER_TEXT,
    STREAMING_TRIGGER_TEXT,
    STRUCTURED_RESULT_TRIGGER_TEXT,
)

pytestmark = pytest.mark.filterwarnings(
    "ignore:label\\(\\) is deprecated\\. Use is_required\\(\\) or is_repeated\\(\\) instead\\.:DeprecationWarning"
)


def _message(
    text: str = "hello",
    *,
    task_id: str = "",
    context_id: str = "",
    parts: list[Part] | None = None,
) -> Message:
    return Message(
        role=Role.ROLE_USER,
        message_id=str(uuid.uuid4()),
        task_id=task_id,
        context_id=context_id,
        parts=parts if parts is not None else [Part(text=text)],
    )


def _send_request(
    text: str = "hello",
    *,
    task_id: str = "",
    context_id: str = "",
    parts: list[Part] | None = None,
) -> SendMessageRequest:
    return SendMessageRequest(
        message=_message(
            text,
            task_id=task_id,
            context_id=context_id,
            parts=parts,
        )
    )


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


async def _stream_rpc(
    client: httpx.AsyncClient,
    method: str,
    params: object,
    request_id: str = "request-1",
) -> list[dict]:
    events: list[dict] = []
    async with client.stream(
        "POST",
        "/rpc",
        json=_rpc_request(method, params, request_id),
        headers={"A2A-Version": "1.0", "Accept": "text/event-stream"},
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
    return events


async def _stream_rest(
    client: httpx.AsyncClient,
    params: SendMessageRequest,
) -> list[dict]:
    events: list[dict] = []
    async with client.stream(
        "POST",
        "/rest/message:stream",
        json=MessageToDict(params),
        headers={"A2A-Version": "1.0", "Accept": "text/event-stream"},
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
    return events


async def _subscribe_rest(
    client: httpx.AsyncClient,
    task_id: str,
) -> list[dict]:
    events: list[dict] = []
    async with client.stream(
        "GET",
        f"/rest/tasks/{task_id}:subscribe",
        headers={"A2A-Version": "1.0", "Accept": "text/event-stream"},
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
    return events


async def _list_rest_tasks(client: httpx.AsyncClient) -> list[dict]:
    response = await client.get(
        "/rest/tasks",
        headers={"A2A-Version": "1.0"},
    )
    assert response.status_code == 200
    return response.json()["tasks"]


async def _wait_for_task_state(
    client: httpx.AsyncClient,
    expected_state: str,
) -> dict:
    async def wait() -> dict:
        while True:
            tasks = await _list_rest_tasks(client)
            for task in tasks:
                if task["status"]["state"] == expected_state:
                    return task
            await asyncio.sleep(0)

    return await asyncio.wait_for(wait(), timeout=1)


def _history_text(task: dict) -> list[str]:
    return [
        message["parts"][0]["text"]
        for message in task["history"]
        if message.get("parts") and "text" in message["parts"][0]
    ]


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
async def test_jsonrpc_continues_input_required_task(
    a2a_client: httpx.AsyncClient,
) -> None:
    first_response = await _post_rpc(
        a2a_client,
        "SendMessage",
        _send_request(INPUT_REQUIRED_TRIGGER_TEXT),
    )
    first_task = first_response["result"]["task"]
    assert first_task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"

    second_response = await _post_rpc(
        a2a_client,
        "SendMessage",
        _send_request(
            "additional input",
            task_id=first_task["id"],
            context_id=first_task["contextId"],
        ),
        request_id="continue-task",
    )
    second_task = second_response["result"]["task"]

    assert second_task["id"] == first_task["id"]
    assert second_task["contextId"] == first_task["contextId"]
    assert second_task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert [message["parts"][0]["text"] for message in second_task["history"]] == [
        INPUT_REQUIRED_TRIGGER_TEXT,
        "More information required",
        "additional input",
        "Echo: additional input",
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_continues_input_required_task(
    a2a_client: httpx.AsyncClient,
) -> None:
    first_response = await a2a_client.post(
        "/rest/message:send",
        json=MessageToDict(_send_request(INPUT_REQUIRED_TRIGGER_TEXT)),
        headers={"A2A-Version": "1.0"},
    )
    assert first_response.status_code == 200
    first_task = first_response.json()["task"]
    assert first_task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"

    second_response = await a2a_client.post(
        "/rest/message:send",
        json=MessageToDict(
            _send_request(
                "additional input",
                task_id=first_task["id"],
                context_id=first_task["contextId"],
            )
        ),
        headers={"A2A-Version": "1.0"},
    )
    assert second_response.status_code == 200
    second_task = second_response.json()["task"]

    assert second_task["id"] == first_task["id"]
    assert second_task["contextId"] == first_task["contextId"]
    assert second_task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert _history_text(second_task) == [
        INPUT_REQUIRED_TRIGGER_TEXT,
        "More information required",
        "additional input",
        "Echo: additional input",
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_returns_structured_completion_artifact_and_status_message(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await _post_rpc(
        a2a_client,
        "SendMessage",
        _send_request(STRUCTURED_RESULT_TRIGGER_TEXT),
    )
    task = response["result"]["task"]

    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert task["status"]["message"]["parts"] == [
        {"text": "Completed with structured data"}
    ]
    assert task["artifacts"][0]["name"] == "Result"
    result_part = task["artifacts"][0]["parts"][0]
    assert result_part["data"] == {"answer": 42.0}
    assert result_part["metadata"]["mimeType"] == "application/json"
    assert result_part["metadata"]["type"] == "object"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_returns_structured_completion_artifact_and_status_message(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await a2a_client.post(
        "/rest/message:send",
        json=MessageToDict(_send_request(STRUCTURED_RESULT_TRIGGER_TEXT)),
        headers={"A2A-Version": "1.0"},
    )
    assert response.status_code == 200
    task = response.json()["task"]

    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert task["status"]["message"]["parts"] == [
        {"text": "Completed with structured data"}
    ]
    result_part = task["artifacts"][0]["parts"][0]
    assert result_part["data"] == {"answer": 42.0}
    assert result_part["metadata"]["mimeType"] == "application/json"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["jsonrpc", "rest"])
async def test_message_parts_round_trip_through_protocol(
    a2a_client: httpx.AsyncClient,
    transport: str,
) -> None:
    request = _send_request(
        parts=[
            Part(text=PARTS_TRIGGER_TEXT),
            Part(
                url="https://example.com/image.png",
                media_type="image/png",
                filename="image.png",
            ),
            Part(
                raw=b"file contents",
                media_type="application/octet-stream",
                filename="data.bin",
            ),
            Part(
                data=ParseDict({"answer": 42}, Value()),
                media_type="application/json",
                filename="result.json",
            ),
        ]
    )

    if transport == "jsonrpc":
        response = await _post_rpc(a2a_client, "SendMessage", request)
        task = response["result"]["task"]
    else:
        response = await a2a_client.post(
            "/rest/message:send",
            json=MessageToDict(request),
            headers={"A2A-Version": "1.0"},
        )
        assert response.status_code == 200
        task = response.json()["task"]

    parts = task["history"][1]["parts"]
    assert parts[0] == {"text": PARTS_TRIGGER_TEXT}
    assert parts[1] == {
        "url": "https://example.com/image.png",
        "mediaType": "image/png",
        "filename": "image.png",
    }
    assert parts[2] == {
        "raw": base64.b64encode(b"file contents").decode(),
        "mediaType": "application/octet-stream",
        "filename": "data.bin",
    }
    assert parts[3]["data"] == {"answer": 42.0}
    assert parts[3]["mediaType"] == "application/json"
    assert parts[3]["filename"] == "result.json"


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
@pytest.mark.parametrize("transport", ["jsonrpc", "rest"])
async def test_cancel_active_task_persists_canceled_state(
    a2a_harness: A2ATestHarness,
    transport: str,
) -> None:
    client = a2a_harness.client
    request = _send_request(LONG_RUNNING_TRIGGER_TEXT)

    if transport == "jsonrpc":
        send_call = asyncio.create_task(_post_rpc(client, "SendMessage", request))
    else:
        send_call = asyncio.create_task(
            client.post(
                "/rest/message:send",
                json=MessageToDict(request),
                headers={"A2A-Version": "1.0"},
            )
        )

    await asyncio.wait_for(a2a_harness.long_running_started.wait(), timeout=1)
    active_task = await _wait_for_task_state(client, "TASK_STATE_WORKING")

    if transport == "jsonrpc":
        cancel_response = await _post_rpc(
            client,
            "CancelTask",
            CancelTaskRequest(id=active_task["id"]),
            request_id="cancel-active",
        )
    else:
        cancel_response = await client.post(
            f"/rest/tasks/{active_task['id']}:cancel",
            headers={"A2A-Version": "1.0"},
        )

    a2a_harness.release_long_running.set()
    send_result = await asyncio.wait_for(send_call, timeout=1)

    if transport == "jsonrpc":
        canceled_task = cancel_response["result"]
        send_task = send_result["result"]["task"]
    else:
        assert cancel_response.status_code == 200
        canceled_task = cancel_response.json()
        assert send_result.status_code == 200
        send_task = send_result.json()["task"]

    assert canceled_task["status"]["state"] == "TASK_STATE_CANCELED"
    assert send_task["status"]["state"] == "TASK_STATE_CANCELED"

    persisted = await client.get(
        f"/rest/tasks/{active_task['id']}",
        headers={"A2A-Version": "1.0"},
    )
    assert persisted.status_code == 200
    assert persisted.json()["status"]["state"] == "TASK_STATE_CANCELED"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["jsonrpc", "rest"])
async def test_agent_failure_returns_protocol_error_and_persists_failed_task(
    a2a_client: httpx.AsyncClient,
    transport: str,
) -> None:
    request = _send_request(FAILURE_TRIGGER_TEXT)

    if transport == "jsonrpc":
        response = await _post_rpc(a2a_client, "SendMessage", request)
        assert "error" in response
    else:
        response = await a2a_client.post(
            "/rest/message:send",
            json=MessageToDict(request),
            headers={"A2A-Version": "1.0"},
        )
        assert response.status_code == 500

    tasks = await _list_rest_tasks(a2a_client)
    assert len(tasks) == 1
    assert tasks[0]["status"]["state"] == "TASK_STATE_FAILED"
    assert _history_text(tasks[0]) == [FAILURE_TRIGGER_TEXT]


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_streaming_message_emits_ordered_task_events(
    a2a_client: httpx.AsyncClient,
) -> None:
    events = await _stream_rpc(
        a2a_client,
        "SendStreamingMessage",
        _send_request(STREAMING_TRIGGER_TEXT),
        request_id="stream-1",
    )

    assert [event["id"] for event in events] == ["stream-1"] * len(events)

    # First event is the newly created task in the submitted state.
    task = events[0]["result"]["task"]
    task_id = task["id"]
    assert task["status"]["state"] == "TASK_STATE_SUBMITTED"

    # The queued informative update surfaces as a "working" status update
    # carrying the informative text as an agent message, before any content.
    working_update = events[1]["result"]["statusUpdate"]
    assert working_update["taskId"] == task_id
    assert working_update["status"]["state"] == "TASK_STATE_WORKING"
    assert working_update["status"]["message"]["parts"][0]["text"] == "Thinking..."

    # The queued text chunks are combined into a single artifact update.
    artifact_update = events[2]["result"]["artifactUpdate"]
    assert artifact_update["taskId"] == task_id
    assert artifact_update["artifact"]["parts"][0]["text"] == (
        f"Echo: {STREAMING_TRIGGER_TEXT}"
    )

    # The stream ends with a "completed" status update once end_stream()
    # finishes and the end-of-conversation activity is processed.
    final_update = events[-1]["result"]["statusUpdate"]
    assert final_update["taskId"] == task_id
    assert final_update["status"]["state"] == "TASK_STATE_COMPLETED"

    # The persisted task reflects the same terminal state via a plain GetTask.
    get_response = await _post_rpc(
        a2a_client,
        "GetTask",
        GetTaskRequest(id=task_id),
        request_id="get-task",
    )
    assert get_response["result"]["status"]["state"] == "TASK_STATE_COMPLETED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_streaming_message_emits_ordered_task_events(
    a2a_client: httpx.AsyncClient,
) -> None:
    events = await _stream_rest(
        a2a_client,
        _send_request(STREAMING_TRIGGER_TEXT),
    )

    task = events[0]["task"]
    task_id = task["id"]
    assert task["status"]["state"] == "TASK_STATE_SUBMITTED"

    working_update = events[1]["statusUpdate"]
    assert working_update["taskId"] == task_id
    assert working_update["status"]["state"] == "TASK_STATE_WORKING"
    assert working_update["status"]["message"]["parts"][0]["text"] == "Thinking..."

    artifact_update = events[2]["artifactUpdate"]
    assert artifact_update["taskId"] == task_id
    assert artifact_update["artifact"]["parts"][0]["text"] == (
        f"Echo: {STREAMING_TRIGGER_TEXT}"
    )

    final_update = events[-1]["statusUpdate"]
    assert final_update["taskId"] == task_id
    assert final_update["status"]["state"] == "TASK_STATE_COMPLETED"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["jsonrpc", "rest"])
async def test_subscribe_to_active_task_streams_initial_and_completed_state(
    a2a_harness: A2ATestHarness,
    transport: str,
) -> None:
    client = a2a_harness.client
    send_call = asyncio.create_task(
        client.post(
            "/rest/message:send",
            json=MessageToDict(_send_request(LONG_RUNNING_TRIGGER_TEXT)),
            headers={"A2A-Version": "1.0"},
        )
    )

    await asyncio.wait_for(a2a_harness.long_running_started.wait(), timeout=1)
    active_task = await _wait_for_task_state(client, "TASK_STATE_WORKING")

    if transport == "jsonrpc":
        subscribe_call = asyncio.create_task(
            _stream_rpc(
                client,
                "SubscribeToTask",
                SubscribeToTaskRequest(id=active_task["id"]),
                request_id="subscribe-task",
            )
        )
    else:
        subscribe_call = asyncio.create_task(_subscribe_rest(client, active_task["id"]))

    await asyncio.sleep(0.05)
    a2a_harness.release_long_running.set()

    events = await asyncio.wait_for(subscribe_call, timeout=1)
    send_response = await asyncio.wait_for(send_call, timeout=1)
    assert send_response.status_code == 200

    if transport == "jsonrpc":
        initial_task = events[0]["result"]["task"]
        terminal_update = events[-1]["result"]["statusUpdate"]
    else:
        initial_task = events[0]["task"]
        terminal_update = events[-1]["statusUpdate"]

    assert initial_task["id"] == active_task["id"]
    assert initial_task["status"]["state"] == "TASK_STATE_WORKING"
    assert terminal_update["status"]["state"] == "TASK_STATE_COMPLETED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_push_notification_config_is_explicitly_unsupported(
    a2a_client: httpx.AsyncClient,
) -> None:
    """The adapter's agent card does not advertise push-notification
    capability, so every push-notification method must fail with the
    protocol-defined PUSH_NOTIFICATION_NOT_SUPPORTED error rather than a
    generic failure or a silent no-op."""

    response = await _post_rpc(
        a2a_client,
        "CreateTaskPushNotificationConfig",
        {"taskId": "missing-task", "url": "https://example.com/webhook"},
        request_id="push-create",
    )

    assert response["error"]["code"] == -32003
    assert response["error"]["message"] == (
        "Push notifications are not supported by the agent"
    )
    error_details = response["error"]["data"][0]
    assert error_details["reason"] == "PUSH_NOTIFICATION_NOT_SUPPORTED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_push_notification_config_is_explicitly_unsupported(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await a2a_client.post(
        "/rest/tasks/missing-task/pushNotificationConfigs",
        json={"url": "https://example.com/webhook"},
        headers={"A2A-Version": "1.0"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["status"] == "FAILED_PRECONDITION"
    assert payload["error"]["details"][0]["reason"] == (
        "PUSH_NOTIFICATION_NOT_SUPPORTED"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonrpc_extended_agent_card_is_explicitly_unconfigured(
    a2a_client: httpx.AsyncClient,
) -> None:
    """The basic agent card advertises `capabilities.extended_agent_card`,
    but the adapter never configures an actual extended card or modifier on
    the request handler, so retrieval must fail with the protocol-defined
    EXTENDED_AGENT_CARD_NOT_CONFIGURED error."""

    response = await _post_rpc(
        a2a_client,
        "GetExtendedAgentCard",
        GetExtendedAgentCardRequest(),
        request_id="extended-card",
    )

    assert response["error"]["code"] == -32007
    error_details = response["error"]["data"][0]
    assert error_details["reason"] == "EXTENDED_AGENT_CARD_NOT_CONFIGURED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_extended_agent_card_is_explicitly_unconfigured(
    a2a_client: httpx.AsyncClient,
) -> None:
    response = await a2a_client.get(
        "/rest/extendedAgentCard",
        headers={"A2A-Version": "1.0"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["status"] == "FAILED_PRECONDITION"
    assert payload["error"]["details"][0]["reason"] == (
        "EXTENDED_AGENT_CARD_NOT_CONFIGURED"
    )
