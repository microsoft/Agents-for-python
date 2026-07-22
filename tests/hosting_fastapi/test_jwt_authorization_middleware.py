# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

import pytest
from fastapi import Request

from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.http import HttpResponse
from microsoft_agents.hosting.fastapi.jwt_authorization_middleware import (
    JwtAuthorizationMiddleware,
    jwt_authorization_decorator,
)


def _scope(auth_config: AgentAuthConfiguration, authorization: str | None = None):
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
        "app": SimpleNamespace(
            state=SimpleNamespace(agent_configuration=auth_config)
        ),
        "state": {},
    }


async def _receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send_ok(send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def _record_send(messages, message):
    messages.append(message)


def _status(messages):
    return next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )


@pytest.mark.asyncio
async def test_fastapi_middleware_stores_claims_and_calls_downstream_app():
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "app-id"}, True)
    messages = []
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True
        assert scope["state"]["claims_identity"] is claims
        await _send_ok(send)

    middleware = JwtAuthorizationMiddleware(downstream)
    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        scope = _scope(auth_config, "Bearer token")
        await middleware(scope, _receive, lambda message: _record_send(messages, message))

    assert downstream_called is True
    assert _status(messages) == 200
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_fastapi_middleware_converts_http_response_without_calling_downstream_app():
    auth_config = AgentAuthConfiguration()
    messages = []
    downstream = AsyncMock()
    middleware = JwtAuthorizationMiddleware(downstream)

    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Invalid token or authentication failed."},
                status_code=401,
            )
        ),
    ) as authorize:
        await middleware(
            _scope(auth_config, "Bearer bad"),
            _receive,
            lambda message: _record_send(messages, message),
        )

    assert _status(messages) == 401
    downstream.assert_not_awaited()
    authorize.assert_awaited_once_with("Bearer bad", auth_config)


@pytest.mark.asyncio
async def test_fastapi_decorator_stores_claims_and_calls_handler():
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "decorator-app"}, True)

    @jwt_authorization_decorator
    async def route(request: Request):
        return {"aud": request.state.claims_identity.claims["aud"]}

    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await route(Request(_scope(auth_config, "Bearer token")))

    assert response == {"aud": "decorator-app"}
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_fastapi_decorator_converts_http_response():
    auth_config = AgentAuthConfiguration()

    @jwt_authorization_decorator
    async def route(request: Request):
        return {"called": True}

    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Authorization header not found"},
                status_code=401,
            )
        ),
    ) as authorize:
        response = await route(Request(_scope(auth_config)))

    assert response.status_code == 401
    assert response.body == b'{"error":"Authorization header not found"}'
    authorize.assert_awaited_once_with(None, auth_config)
