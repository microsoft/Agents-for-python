# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import uuid
from unittest.mock import MagicMock

import pytest
from a2a.types import AgentInterface, Message, Part, Role, SendMessageRequest
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.protobuf.json_format import MessageToDict

from microsoft_agents.activity import Activity, ActivityTypes, EndOfConversationCodes
from microsoft_agents.hosting.a2a import A2AAdapter, add_a2a
from microsoft_agents.hosting.core import (
    AgentApplication,
    ApplicationOptions,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from tests.utils.config import REAL_SERVICE_CONNECTION_ENV_VARS
from tests.utils.pytest import skip_if_no_var

from ._helpers import (
    acquire_real_service_connection_token,
    auth_config_with_invalid_audience,
)

_requires_real_service_connection = skip_if_no_var(
    *REAL_SERVICE_CONNECTION_ENV_VARS, load_root_env_file=True
)


def _rpc_request() -> dict:
    request = SendMessageRequest(
        message=Message(
            role=Role.ROLE_USER,
            message_id=str(uuid.uuid4()),
            parts=[Part(text="hello")],
        )
    )
    return {
        "jsonrpc": "2.0",
        "id": "request-1",
        "method": "SendMessage",
        "params": MessageToDict(request),
    }


def _create_app(auth_config):
    observed = {}
    agent = AgentApplication[TurnState](
        options=ApplicationOptions(storage=MemoryStorage()),
        connection_manager=MagicMock(),
    )

    @agent.activity(ActivityTypes.message)
    async def on_message(context: TurnContext, _state: TurnState) -> None:
        observed["identity"] = context.identity
        await context.send_activity("Authenticated")
        await context.send_activity(
            Activity(
                type=ActivityTypes.end_of_conversation,
                code=EndOfConversationCodes.completed_successfully,
            )
        )

    app = FastAPI()
    app.state.agent_configuration = auth_config
    adapter = A2AAdapter(
        agent,
        agent_interfaces=[
            AgentInterface(
                url="/a2a",
                protocol_binding=TransportProtocol.JSONRPC,
            )
        ],
    )
    add_a2a(app, agent, adapter=adapter)
    return app, observed


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_a2a_accepts_real_service_connection_token_and_forwards_identity():
    token, auth_config = await acquire_real_service_connection_token()
    app, observed = _create_app(auth_config)

    with TestClient(app) as client:
        response = client.post(
            "/a2a",
            json=_rpc_request(),
            headers={
                "A2A-Version": "1.0",
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 200
    assert response.json()["result"]["task"]["status"]["state"] == (
        "TASK_STATE_COMPLETED"
    )
    identity = observed["identity"]
    assert identity.allow_anonymous is False
    assert identity.claims


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_a2a_rejects_real_token_with_invalid_audience():
    token, auth_config = await acquire_real_service_connection_token()
    app, observed = _create_app(auth_config_with_invalid_audience(auth_config))

    with TestClient(app) as client:
        response = client.post(
            "/a2a",
            json=_rpc_request(),
            headers={
                "A2A-Version": "1.0",
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid token or authentication failed."}
    assert "identity" not in observed
