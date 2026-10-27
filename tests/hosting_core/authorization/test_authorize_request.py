# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib
import gc
import weakref
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core.authorization import (
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request
from microsoft_agents.hosting.core.http import HttpResponse
from tests._common.jwt_test_utils import make_jwt_configuration

_authorize_request_module = importlib.import_module(
    "microsoft_agents.hosting.core.authorization.jwt._authorize_request"
)


class _CacheOwner:
    def __bool__(self):
        return False


@dataclass
class _UnhashableCacheOwner:
    pass


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
    result = await _authorize_request(None, make_jwt_configuration())

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Authorization header not found"}


@pytest.mark.asyncio
async def test_authorize_request_returns_anonymous_claims_when_header_is_missing_and_anonymous_enabled():
    auth_config = make_jwt_configuration(anonymous_allowed=True)
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
    result = await _authorize_request("Basic token", make_jwt_configuration())

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Invalid authorization header format"}


@pytest.mark.asyncio
async def test_authorize_request_validates_bearer_token():
    auth_config = make_jwt_configuration()
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
async def test_authorize_request_returns_401_when_token_validation_fails():
    validator = MagicMock()
    validator.validate_token = AsyncMock(side_effect=ValueError("bad token"))

    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        return_value=validator,
    ):
        result = await _authorize_request(
            "Bearer token-value", make_jwt_configuration()
        )

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Invalid token or authentication failed."}
    validator.validate_token.assert_awaited_once_with("token-value")


@pytest.mark.asyncio
async def test_cache_normalizes_mapping_and_constructs_validator_only_once():
    owner = _CacheOwner()
    auth_config = {"TOKEN_VALIDATION": {"ANONYMOUS_ALLOWED": True}}

    with (
        patch.object(
            _authorize_request_module, "Configuration", wraps=Configuration
        ) as configuration,
        patch.object(
            _authorize_request_module,
            "JwtTokenValidator",
            wraps=_authorize_request_module.JwtTokenValidator,
        ) as factory,
    ):
        first = await _authorize_request(None, auth_config, cache_key=owner)
        second = await _authorize_request(None, cache_key=owner)

    assert first.allow_anonymous
    assert second.allow_anonymous
    assert first is not second
    configuration.assert_called_once_with(auth_config)
    factory.assert_called_once_with(Configuration(auth_config))


@pytest.mark.asyncio
async def test_cache_is_isolated_by_owner():
    first_owner = _CacheOwner()
    second_owner = _CacheOwner()
    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        wraps=_authorize_request_module.JwtTokenValidator,
    ) as factory:
        first = await _authorize_request(
            None, make_jwt_configuration(anonymous_allowed=True), cache_key=first_owner
        )
        second = await _authorize_request(
            None, make_jwt_configuration(), cache_key=second_owner
        )
        again = await _authorize_request(None, cache_key=first_owner)

    assert first.allow_anonymous
    assert second.status_code == 401
    assert again.allow_anonymous
    assert factory.call_count == 2


@pytest.mark.asyncio
async def test_calls_without_cache_key_construct_validator_each_time():
    auth_config = make_jwt_configuration()
    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        wraps=_authorize_request_module.JwtTokenValidator,
    ) as factory:
        await _authorize_request(None, auth_config)
        await _authorize_request(None, auth_config)

    assert factory.call_count == 2


@pytest.mark.asyncio
async def test_explicit_validator_takes_precedence_without_replacing_cached_validator():
    owner = _CacheOwner()
    await _authorize_request(
        None, make_jwt_configuration(anonymous_allowed=True), cache_key=owner
    )
    validator = MagicMock()
    validator.config.anonymous_allowed = False

    with patch.object(_authorize_request_module, "JwtTokenValidator") as factory:
        explicit_result = await _authorize_request(
            None, validator=validator, cache_key=owner
        )
        cached_result = await _authorize_request(None, cache_key=owner)

    assert explicit_result.status_code == 401
    assert cached_result.allow_anonymous
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_cache_does_not_retain_owner():
    owner = _CacheOwner()
    await _authorize_request(None, make_jwt_configuration(), cache_key=owner)
    validator = _authorize_request_module._TOKEN_VALIDATOR_CACHE[owner]
    reference = weakref.ref(owner)

    del owner
    gc.collect()

    assert reference() is None
    assert validator not in _authorize_request_module._TOKEN_VALIDATOR_CACHE.values()


@pytest.mark.asyncio
async def test_failed_construction_does_not_populate_cache():
    owner = _CacheOwner()
    auth_config = make_jwt_configuration()
    with patch.object(
        _authorize_request_module,
        "JwtTokenValidator",
        side_effect=ValueError("invalid"),
    ):
        with pytest.raises(ValueError, match="invalid"):
            await _authorize_request(None, auth_config, cache_key=owner)

    assert owner not in _authorize_request_module._TOKEN_VALIDATOR_CACHE
    result = await _authorize_request(None, auth_config, cache_key=owner)
    assert result.status_code == 401


@pytest.mark.asyncio
async def test_cache_owner_without_configuration_uses_empty_policy():
    result = await _authorize_request(None, cache_key=_CacheOwner())

    assert result.status_code == 401
    assert result.body == {"error": "Authorization header not found"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cache_key",
    [{}, "invalid-key", _UnhashableCacheOwner()],
    ids=["mapping", "string", "unhashable-owner"],
)
async def test_invalid_cache_key_raises_without_constructing_validator(cache_key):
    with patch.object(_authorize_request_module, "JwtTokenValidator") as factory:
        with pytest.raises(TypeError):
            await _authorize_request(
                None, make_jwt_configuration(), cache_key=cache_key
            )

    factory.assert_not_called()
