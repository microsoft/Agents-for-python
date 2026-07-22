# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from fastapi import FastAPI, Request

from microsoft_agents.hosting.fastapi import JwtAuthorizationMiddleware

from ._helpers import load_auth_config


def _scope(app: FastAPI, authorization: str | None = None):
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
        "scheme": "http",
        "app": app,
        "state": {},
    }


async def _receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send_json(send, status: int, body: bytes):
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _record_send(messages, message):
    messages.append(message)


def _status(messages):
    return next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )


def _body(messages):
    return b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )


@pytest.mark.asyncio
async def test_fastapi_jwt_allows_anonymous_request_from_env_config():
    app = FastAPI()
    app.state.agent_configuration = load_auth_config("jwt_anonymous.env")
    messages = []

    async def downstream(scope, receive, send):
        request = Request(scope, receive=receive)
        identity = request.state.claims_identity
        await _send_json(
            send,
            200,
            (
                b'{"authenticated":'
                + str(identity.is_authenticated).lower().encode()
                + b',"authentication_type":"'
                + identity.authentication_type.encode()
                + b'"}'
            ),
        )

    middleware = JwtAuthorizationMiddleware(downstream)
    await middleware(
        _scope(app),
        _receive,
        lambda message: _record_send(messages, message),
    )

    assert _status(messages) == 200
    assert _body(messages) == (
        b'{"authenticated":false,"authentication_type":"Anonymous"}'
    )


@pytest.mark.asyncio
async def test_fastapi_jwt_rejects_missing_authorization_header():
    app = FastAPI()
    app.state.agent_configuration = load_auth_config("jwt_required.env")
    messages = []
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True
        await _send_json(send, 200, b'{"called":true}')

    middleware = JwtAuthorizationMiddleware(downstream)
    await middleware(
        _scope(app),
        _receive,
        lambda message: _record_send(messages, message),
    )

    assert downstream_called is False
    assert _status(messages) == 401
    assert _body(messages) == b'{"error":"Authorization header not found"}'


@pytest.mark.asyncio
async def test_fastapi_jwt_rejects_invalid_bearer_token():
    app = FastAPI()
    app.state.agent_configuration = load_auth_config("jwt_required.env")
    messages = []
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True
        await _send_json(send, 200, b'{"called":true}')

    middleware = JwtAuthorizationMiddleware(downstream)
    await middleware(
        _scope(app, "Bearer not-a-jwt"),
        _receive,
        lambda message: _record_send(messages, message),
    )

    assert downstream_called is False
    assert _status(messages) == 401
    assert _body(messages) == b'{"error":"Invalid token or authentication failed."}'
