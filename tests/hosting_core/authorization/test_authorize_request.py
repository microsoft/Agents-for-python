# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib
from unittest.mock import AsyncMock, MagicMock, patch
from weakref import ref

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request
from microsoft_agents.hosting.core.http import HttpResponse
from tests._common.jwt_test_utils import generate_rsa_keypair, make_signed_jwt

_authorize_request_module = importlib.import_module(
    "microsoft_agents.hosting.core.authorization.jwt._authorize_request"
)


@pytest.mark.asyncio
async def test_authorize_request_returns_500_when_config_is_missing():
    with patch.object(_authorize_request_module, "JwtTokenValidator") as validator_cls:
        result = await _authorize_request("Bearer token", None)

    assert isinstance(result, HttpResponse)
    assert result.status_code == 500
    assert result.body == {"error": "Agent Authentication configuration not found"}
    validator_cls.assert_not_called()


@pytest.mark.asyncio
async def test_authorize_request_returns_401_when_header_is_missing_and_anonymous_disabled():
    result = await _authorize_request(None, AgentAuthConfiguration())

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Authorization header not found"}


@pytest.mark.asyncio
async def test_authorize_request_returns_anonymous_claims_when_header_is_missing_and_anonymous_enabled():
    auth_config = AgentAuthConfiguration(anonymous_allowed=True)
    claims = ClaimsIdentity({}, authentication_type="Anonymous")
    validator = MagicMock()
    validator.get_anonymous_claims.return_value = claims

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        return_value=validator,
    ) as validator_cls:
        result = await _authorize_request(None, auth_config)

    assert result is claims
    validator_cls.assert_called_once_with(auth_config)
    validator.get_anonymous_claims.assert_called_once_with()


@pytest.mark.asyncio
async def test_authorize_request_returns_401_for_invalid_authorization_header_format():
    result = await _authorize_request("Basic token", AgentAuthConfiguration())

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Invalid authorization header format"}


@pytest.mark.asyncio
async def test_authorize_request_validates_bearer_token():
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "app-id"}, authentication_type="Bearer")
    validator = MagicMock()
    validator.validate_token = AsyncMock(return_value=claims)

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        return_value=validator,
    ) as validator_cls:
        result = await _authorize_request("Bearer token-value", auth_config)

    assert result is claims
    validator_cls.assert_called_once_with(auth_config)
    validator.validate_token.assert_awaited_once_with("token-value")


@pytest.mark.asyncio
@pytest.mark.parametrize("anonymous_allowed", [True, False])
async def test_root_configuration_anonymous_policy_overrides_service_connection(
    anonymous_allowed,
):
    config = Configuration(
        connections={
            "SERVICE_CONNECTION": {
                "settings": {"anonymous_allowed": not anonymous_allowed}
            }
        },
        token_validation={"anonymous_allowed": anonymous_allowed},
    )
    result = await _authorize_request(None, config)
    if anonymous_allowed:
        assert isinstance(result, ClaimsIdentity)
        assert result.allow_anonymous is True
    else:
        assert isinstance(result, HttpResponse)
        assert result.status_code == 401


@pytest.mark.asyncio
async def test_root_configuration_authorizes_signed_token(monkeypatch):
    config = Configuration(
        connections={"SERVICE_CONNECTION": {"settings": {"client_id": "client"}}}
    )
    private_key, public_key = generate_rsa_keypair()

    async def get_signing_key(uri, header):
        return public_key

    monkeypatch.setattr(
        _authorize_request_module.JwtTokenValidator._jwk_client_manager,
        "get_signing_key",
        get_signing_key,
    )
    token = make_signed_jwt(private_key, {"aud": "client"})
    result = await _authorize_request(f"Bearer {token}", config)
    assert isinstance(result, ClaimsIdentity)
    assert result.claims["aud"] == "client"
    assert result.allow_anonymous is False


def test_validator_cache_reuses_same_owner_and_isolates_different_owners():
    class Owner:
        pass

    first_owner, second_owner = Owner(), Owner()
    config = Configuration(token_validation={"anonymous_allowed": True})
    resolve = _authorize_request_module._resolve_token_validator
    first = resolve(config, first_owner)
    assert resolve(config, first_owner) is first
    assert resolve(config, second_owner) is not first
    assert resolve(config) is not resolve(config)


def test_validator_cache_does_not_retain_owner():
    class Owner:
        pass

    owner = Owner()
    owner_ref = ref(owner)
    validator = _authorize_request_module._resolve_token_validator(
        Configuration(), owner
    )
    cache = _authorize_request_module._TOKEN_VALIDATION_CACHE
    assert cache[owner] is validator
    del owner
    assert owner_ref() is None
    assert validator not in cache.values()


@pytest.mark.asyncio
async def test_authorize_request_returns_401_when_token_validation_fails():
    validator = MagicMock()
    validator.validate_token = AsyncMock(side_effect=ValueError("bad token"))

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        return_value=validator,
    ):
        result = await _authorize_request(
            "Bearer token-value", AgentAuthConfiguration()
        )

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Invalid token or authentication failed."}
    validator.validate_token.assert_awaited_once_with("token-value")
