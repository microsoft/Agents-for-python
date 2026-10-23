# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import gc
import importlib
import json
import weakref
from unittest.mock import AsyncMock, call, patch, sentinel

import pytest
from aiohttp import web
from microsoft_agents.activity.config import Configuration

from microsoft_agents.hosting.aiohttp.jwt_authorization_middleware import (
    jwt_authorization_decorator,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.http import HttpResponse

_jwt_middleware_module = importlib.import_module(
    "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware"
)
_AUTHORIZATION = "Bearer synthetic-token"


def _make_app(auth_config: Configuration) -> web.Application:
    app = web.Application()
    with pytest.warns(web.NotAppKeyWarning):
        app["agent_configuration"] = auth_config
    return app


class _RequestStub:
    def __init__(
        self,
        auth_config: Configuration,
        authorization: str | None = None,
        *,
        app: web.Application | None = None,
    ):
        self.app = app if app is not None else _make_app(auth_config)
        self.headers = {}
        if authorization is not None:
            self.headers["Authorization"] = authorization
        self._items = {}

    def __getitem__(self, key):
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value


def _response_json(response):
    return json.loads(response.body.decode())


@pytest.fixture
def validator_factory():
    with patch.object(
        _jwt_middleware_module, "JwtTokenValidator", autospec=True
    ) as factory:
        yield factory


@pytest.mark.asyncio
async def test_aiohttp_middleware_stores_claims_and_calls_handler(validator_factory):
    auth_config = Configuration()
    claims = ClaimsIdentity({"aud": "app-id"}, authentication_type="Bearer")

    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await _jwt_middleware_module._jwt_authorization_middleware(
            _RequestStub(auth_config, _AUTHORIZATION), handler
        )

    assert response.status == 200
    assert _response_json(response) == {"aud": "app-id"}
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
async def test_aiohttp_middleware_converts_http_response(validator_factory):
    auth_config = Configuration()
    handler = AsyncMock(return_value=web.json_response({"called": True}))

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
        response = await _jwt_middleware_module._jwt_authorization_middleware(
            _RequestStub(auth_config, _AUTHORIZATION), handler
        )

    assert response.status == 401
    assert _response_json(response) == {
        "error": "Invalid token or authentication failed."
    }
    handler.assert_not_awaited()
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )


@pytest.mark.asyncio
async def test_aiohttp_decorator_uses_authorization_helper(validator_factory):
    auth_config = Configuration()
    claims = ClaimsIdentity({"aud": "decorator-app"}, authentication_type="Bearer")

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await handler(_RequestStub(auth_config, _AUTHORIZATION))

    assert response.status == 200
    assert _response_json(response) == {"aud": "decorator-app"}
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, validator=validator_factory.return_value
    )


@pytest.mark.asyncio
async def test_aiohttp_decorator_converts_http_response(validator_factory):
    auth_config = Configuration()

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"called": True})

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
        response = await handler(_RequestStub(auth_config))

    assert response.status == 401
    assert _response_json(response) == {"error": "Authorization header not found"}
    authorize.assert_awaited_once_with(None, validator=validator_factory.return_value)


def test_aiohttp_frozen_app_binds_configuration_and_validator_only_once(
    validator_factory,
):
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)
    app.freeze()

    with patch.object(
        _jwt_middleware_module, "Configuration", wraps=Configuration
    ) as configuration:
        first = _jwt_middleware_module._get_or_create_cached_validator(app)
        second = _jwt_middleware_module._get_or_create_cached_validator(app)

    assert first is second is validator_factory.return_value
    configuration.assert_called_once_with(auth_config)
    validator_factory.assert_called_once_with(auth_config)


def test_aiohttp_validator_cache_is_isolated_per_app(validator_factory):
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


def test_aiohttp_validator_cache_does_not_retain_applications(validator_factory):
    app = _make_app(Configuration())
    _jwt_middleware_module._get_or_create_cached_validator(app)
    reference = weakref.ref(app)

    del app
    gc.collect()

    assert reference() is None


@pytest.mark.asyncio
async def test_aiohttp_middleware_and_decorator_share_cache_not_claims(
    validator_factory,
):
    auth_config = Configuration()
    app = _make_app(auth_config)
    first = _RequestStub(auth_config, "Bearer first-token", app=app)
    second = _RequestStub(auth_config, "Bearer second-token", app=app)
    first_claims = ClaimsIdentity({"aud": "first"}, authentication_type="Bearer")
    second_claims = ClaimsIdentity({"aud": "second"}, authentication_type="Bearer")

    async def handler(request):
        return web.Response(status=200)

    decorated = jwt_authorization_decorator(handler)
    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(side_effect=[first_claims, second_claims]),
    ) as authorize:
        await _jwt_middleware_module._jwt_authorization_middleware(first, handler)
        await decorated(second)

    assert first["claims_identity"] is first_claims
    assert second["claims_identity"] is second_claims
    authorize.assert_has_awaits(
        [
            call("Bearer first-token", validator=validator_factory.return_value),
            call("Bearer second-token", validator=validator_factory.return_value),
        ]
    )
    assert authorize.await_count == 2
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
async def test_aiohttp_cached_validator_still_rejects_malformed_authorization():
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)

    async def handler(request):
        return web.Response(status=200)

    with patch.object(
        _jwt_middleware_module,
        "JwtTokenValidator",
        wraps=_jwt_middleware_module.JwtTokenValidator,
    ) as factory:
        responses = [
            await _jwt_middleware_module._jwt_authorization_middleware(
                _RequestStub(auth_config, header, app=app), handler
            )
            for header in (None, None, "Basic invalid")
        ]

    assert [response.status for response in responses] == [200, 200, 401]
    factory.assert_called_once_with(auth_config)
