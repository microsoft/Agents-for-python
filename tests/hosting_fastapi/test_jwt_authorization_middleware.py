# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib
import inspect
from unittest.mock import AsyncMock, call, patch, sentinel

import pytest
from fastapi import Depends, FastAPI, Request
from microsoft_agents.activity.config import Configuration

from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.http import HttpResponse
from microsoft_agents.hosting.fastapi.jwt_authorization_middleware import (
    JwtAuthorizationMiddleware,
    jwt_authorization_decorator,
)

_jwt_middleware_module = importlib.import_module(
    "microsoft_agents.hosting.fastapi.jwt_authorization_middleware"
)
_AUTHORIZATION = "Bearer synthetic-token"


def _make_app(auth_config: Configuration | AgentAuthConfiguration) -> FastAPI:
    app = FastAPI()
    app.state.agent_configuration = auth_config
    return app


def _scope(
    auth_config: Configuration | AgentAuthConfiguration,
    authorization: str | None = None,
    *,
    app: FastAPI | None = None,
):
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
        "app": app if app is not None else _make_app(auth_config),
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


@pytest.fixture
def validator_factory():
    with patch.object(
        _jwt_middleware_module, "JwtTokenValidator", autospec=True
    ) as factory:
        yield factory


@pytest.mark.asyncio
async def test_fastapi_middleware_stores_claims_and_calls_downstream_app(
    validator_factory,
):
    auth_config = Configuration()
    claims = ClaimsIdentity({"aud": "app-id"}, authentication_type="Bearer")
    messages = []
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True
        assert scope["state"]["claims_identity"] is claims
        await _send_ok(send)

    middleware = JwtAuthorizationMiddleware(downstream)
    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        scope = _scope(auth_config, _AUTHORIZATION)
        await middleware(
            scope, _receive, lambda message: _record_send(messages, message)
        )

    assert downstream_called is True
    assert _status(messages) == 200
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
async def test_fastapi_middleware_converts_http_response_without_calling_downstream_app(
    validator_factory,
):
    auth_config = Configuration()
    messages = []
    downstream = AsyncMock()
    middleware = JwtAuthorizationMiddleware(downstream)

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Invalid token or authentication failed."},
                status_code=401,
            )
        ),
    ) as authorize:
        await middleware(
            _scope(auth_config, _AUTHORIZATION),
            _receive,
            lambda message: _record_send(messages, message),
        )

    assert _status(messages) == 401
    downstream.assert_not_awaited()
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )


@pytest.mark.asyncio
async def test_fastapi_decorator_stores_claims_and_calls_handler(validator_factory):
    auth_config = Configuration()
    claims = ClaimsIdentity({"aud": "decorator-app"}, authentication_type="Bearer")

    @jwt_authorization_decorator
    async def route(request: Request):
        return {"aud": request.state.claims_identity.claims["aud"]}

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await route(Request(_scope(auth_config, _AUTHORIZATION)))

    assert response == {"aud": "decorator-app"}
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )


@pytest.mark.asyncio
async def test_fastapi_decorator_converts_http_response(validator_factory):
    auth_config = Configuration()

    @jwt_authorization_decorator
    async def route(request: Request):
        return {"called": True}

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
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
    authorize.assert_awaited_once_with(None, validator=validator_factory.return_value)


def test_fastapi_validator_binds_configuration_only_once(validator_factory):
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)

    with patch.object(
        _jwt_middleware_module, "Configuration", wraps=Configuration
    ) as configuration:
        first = _jwt_middleware_module._get_or_create_cached_validator(app)
        second = _jwt_middleware_module._get_or_create_cached_validator(app)

    assert first is second is validator_factory.return_value
    configuration.assert_called_once_with(auth_config)
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
@pytest.mark.parametrize("anonymous_allowed", [True, False])
async def test_fastapi_legacy_configuration_preserves_policy_and_shared_cache(
    anonymous_allowed,
):
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        auth_config = AgentAuthConfiguration(
            client_id="legacy-app",
            tenant_id="legacy-tenant",
            anonymous_allowed=anonymous_allowed,
        )
    app = _make_app(auth_config)
    messages = []

    async def downstream(scope, receive, send):
        assert scope["state"]["claims_identity"].allow_anonymous
        await _send_ok(send)

    @jwt_authorization_decorator
    async def route(request: Request):
        assert request.state.claims_identity.allow_anonymous
        return {"called": True}

    with patch.object(
        _jwt_middleware_module,
        "JwtTokenValidator",
        wraps=_jwt_middleware_module.JwtTokenValidator,
    ) as factory:
        await JwtAuthorizationMiddleware(downstream)(
            _scope(auth_config, app=app),
            _receive,
            lambda message: _record_send(messages, message),
        )
        response = await route(Request(_scope(auth_config, app=app)))
        validator = _jwt_middleware_module._get_or_create_cached_validator(app)

    assert _status(messages) == (200 if anonymous_allowed else 401)
    if anonymous_allowed:
        assert response == {"called": True}
    else:
        assert response.status_code == 401
    factory.assert_called_once_with(auth_config)
    assert factory.call_args.args[0] is auth_config
    assert validator.config.anonymous_allowed is anonymous_allowed
    assert validator.config.audiences == ["legacy-app"]
    assert validator.config.tenant_id == "legacy-tenant"


def test_fastapi_validator_cache_is_isolated_per_app(validator_factory):
    first_app = _make_app(Configuration({"name": "first"}))
    second_app = _make_app(Configuration({"name": "second"}))
    validator_factory.side_effect = [
        sentinel.first_validator,
        sentinel.second_validator,
    ]

    assert (
        _jwt_middleware_module._get_or_create_cached_validator(first_app)
        is sentinel.first_validator
    )
    assert (
        _jwt_middleware_module._get_or_create_cached_validator(second_app)
        is sentinel.second_validator
    )
    assert (
        _jwt_middleware_module._get_or_create_cached_validator(first_app)
        is sentinel.first_validator
    )
    assert validator_factory.call_count == 2


def test_fastapi_preserves_explicitly_supplied_validator(validator_factory):
    app = _make_app(Configuration())
    app.state.jwt_validator = sentinel.preconfigured_validator

    assert (
        _jwt_middleware_module._get_or_create_cached_validator(app)
        is sentinel.preconfigured_validator
    )
    validator_factory.assert_not_called()


@pytest.mark.asyncio
async def test_fastapi_middleware_and_decorator_share_cache_not_claims(
    validator_factory,
):
    auth_config = Configuration()
    app = _make_app(auth_config)
    first_claims = ClaimsIdentity({"aud": "first"}, authentication_type="Bearer")
    second_claims = ClaimsIdentity({"aud": "second"}, authentication_type="Bearer")
    first_scope = _scope(auth_config, "Bearer first-token", app=app)
    second_request = Request(_scope(auth_config, "Bearer second-token", app=app))
    messages = []

    async def downstream(scope, receive, send):
        await _send_ok(send)

    @jwt_authorization_decorator
    async def route(request: Request):
        return request.state.claims_identity

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(side_effect=[first_claims, second_claims]),
    ) as authorize:
        await JwtAuthorizationMiddleware(downstream)(
            first_scope, _receive, lambda message: _record_send(messages, message)
        )
        result = await route(second_request)

    assert first_scope["state"]["claims_identity"] is first_claims
    assert result is second_claims
    assert _status(messages) == 200
    authorize.assert_has_awaits(
        [
            call("Bearer first-token", validator=validator_factory.return_value),
            call("Bearer second-token", validator=validator_factory.return_value),
        ]
    )
    assert authorize.await_count == 2
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
async def test_fastapi_cached_validator_still_rejects_malformed_authorization():
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)

    async def downstream(scope, receive, send):
        await _send_ok(send)

    middleware = JwtAuthorizationMiddleware(downstream)
    statuses = []
    with patch.object(
        _jwt_middleware_module,
        "JwtTokenValidator",
        wraps=_jwt_middleware_module.JwtTokenValidator,
    ) as factory:
        for header in (None, None, "Basic invalid"):
            messages = []
            await middleware(
                _scope(auth_config, header, app=app),
                _receive,
                lambda message: _record_send(messages, message),
            )
            statuses.append(_status(messages))

    assert statuses == [200, 200, 401]
    factory.assert_called_once_with(auth_config)


def test_fastapi_decorator_preserves_route_signature():
    async def route(
        request: Request,
        conversation_id: str,
        include_history: bool = False,
    ) -> dict:
        return {}

    decorated = jwt_authorization_decorator(route)

    assert inspect.signature(decorated, follow_wrapped=False) == inspect.signature(
        route
    )


def test_fastapi_decorator_preserves_route_signature_with_dependencies():
    def get_user_id() -> str:
        return "user-id"

    async def route(
        request: Request,
        user_id: str = Depends(get_user_id),
    ) -> dict:
        return {}

    decorated = jwt_authorization_decorator(route)

    assert inspect.signature(decorated, follow_wrapped=False) == inspect.signature(
        route
    )


def test_fastapi_decorator_does_not_change_original_route_signature():
    async def route(
        request: Request,
        conversation_id: str,
        user_id: str = Depends(lambda: "user-id"),
    ) -> dict:
        return {}

    original_signature = inspect.signature(route)

    jwt_authorization_decorator(route)

    assert inspect.signature(route) == original_signature
