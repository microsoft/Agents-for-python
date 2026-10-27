# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import gc
import importlib
import json
import weakref
from unittest.mock import AsyncMock, call, patch

import pytest
from aiohttp import web
from microsoft_agents.activity.config import Configuration

from microsoft_agents.hosting.aiohttp.jwt_authorization_middleware import (
    jwt_authorization_decorator,
)
from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.http import HttpResponse

_jwt_middleware_module = importlib.import_module(
    "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware"
)
_authorize_request_module = importlib.import_module(
    "microsoft_agents.hosting.core.authorization.jwt._authorize_request"
)
_AUTHORIZATION = "Bearer test-token"


def _make_app(
    auth_config: Configuration | AgentAuthConfiguration,
) -> web.Application:
    app = web.Application()
    with pytest.warns(web.NotAppKeyWarning):
        app["agent_configuration"] = auth_config
    return app


class _RequestStub:
    def __init__(
        self,
        auth_config: Configuration | AgentAuthConfiguration,
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


@pytest.fixture
def validator_factory():
    with patch.object(
        _authorize_request_module, "JwtTokenValidator", autospec=True
    ) as factory:
        yield factory


@pytest.mark.asyncio
@pytest.mark.parametrize("use_decorator", [False, True])
async def test_aiohttp_forwards_configuration_and_cache_key_and_stores_claims(
    use_decorator,
):
    auth_config = Configuration()
    request = _RequestStub(auth_config, _AUTHORIZATION)
    claims = ClaimsIdentity({"aud": "app-id"}, authentication_type="Bearer")

    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        if use_decorator:
            response = await jwt_authorization_decorator(handler)(request)
        else:
            response = await _jwt_middleware_module._jwt_authorization_middleware(
                request, handler
            )

    assert response.status == 200
    assert json.loads(response.body.decode()) == {"aud": "app-id"}
    authorize.assert_awaited_once_with(
        _AUTHORIZATION, auth_config, cache_key=request.app
    )
    assert authorize.call_args.args[1] is auth_config


@pytest.mark.asyncio
@pytest.mark.parametrize("use_decorator", [False, True])
async def test_aiohttp_converts_http_response_without_calling_handler(use_decorator):
    auth_config = Configuration()
    request = _RequestStub(auth_config)
    handler = AsyncMock()

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Authorization header not found"}, status_code=401
            )
        ),
    ) as authorize:
        if use_decorator:
            response = await jwt_authorization_decorator(handler)(request)
        else:
            response = await _jwt_middleware_module._jwt_authorization_middleware(
                request, handler
            )

    assert response.status == 401
    assert json.loads(response.body.decode()) == {
        "error": "Authorization header not found"
    }
    handler.assert_not_awaited()
    authorize.assert_awaited_once_with(None, auth_config, cache_key=request.app)


@pytest.mark.asyncio
async def test_aiohttp_frozen_app_binds_configuration_and_validator_only_once(
    validator_factory,
):
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)
    app.freeze()
    handler = AsyncMock(return_value=web.Response(status=200))

    with patch.object(
        _authorize_request_module, "Configuration", wraps=Configuration
    ) as configuration:
        for _ in range(2):
            await _jwt_middleware_module._jwt_authorization_middleware(
                _RequestStub(auth_config, app=app), handler
            )

    configuration.assert_called_once_with(auth_config)
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
@pytest.mark.parametrize("anonymous_allowed", [True, False])
async def test_aiohttp_legacy_configuration_preserves_policy_and_shared_cache(
    anonymous_allowed,
):
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        auth_config = AgentAuthConfiguration(
            client_id="legacy-app",
            tenant_id="legacy-tenant",
            anonymous_allowed=anonymous_allowed,
        )
    app = _make_app(auth_config)
    app.freeze()

    async def handler(request):
        assert request["claims_identity"].allow_anonymous
        return web.Response(status=200)

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        wraps=_authorize_request_module.JwtTokenValidator,
    ) as factory:
        first = await _jwt_middleware_module._jwt_authorization_middleware(
            _RequestStub(auth_config, app=app), handler
        )
        second = await jwt_authorization_decorator(handler)(
            _RequestStub(auth_config, app=app)
        )
        validator = _authorize_request_module._TOKEN_VALIDATOR_CACHE[app]

    expected_status = 200 if anonymous_allowed else 401
    assert [first.status, second.status] == [expected_status, expected_status]
    factory.assert_called_once_with(auth_config)
    assert factory.call_args.args[0] is auth_config
    assert validator.config.anonymous_allowed is anonymous_allowed
    assert validator.config.audiences == ["legacy-app"]
    assert validator.config.tenant_id == "legacy-tenant"


@pytest.mark.asyncio
async def test_aiohttp_validator_cache_does_not_retain_applications():
    app = _make_app(Configuration())
    await _authorize_request_module._authorize_request(
        None, Configuration(), cache_key=app
    )
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

    validator = validator_factory.return_value
    validator.validate_token.side_effect = [first_claims, second_claims]
    await _jwt_middleware_module._jwt_authorization_middleware(first, handler)
    await jwt_authorization_decorator(handler)(second)

    assert first["claims_identity"] is first_claims
    assert second["claims_identity"] is second_claims
    validator.validate_token.assert_has_awaits(
        [call("first-token"), call("second-token")]
    )
    assert validator.validate_token.await_count == 2
    validator_factory.assert_called_once_with(auth_config)


@pytest.mark.asyncio
async def test_aiohttp_cached_validator_still_rejects_malformed_authorization():
    auth_config = Configuration({"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}})
    app = _make_app(auth_config)

    async def handler(request):
        return web.Response(status=200)

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        wraps=_authorize_request_module.JwtTokenValidator,
    ) as factory:
        responses = [
            await _jwt_middleware_module._jwt_authorization_middleware(
                _RequestStub(auth_config, header, app=app), handler
            )
            for header in (None, None, "Basic invalid")
        ]

    assert [response.status for response in responses] == [200, 200, 401]
    factory.assert_called_once_with(auth_config)
