# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request
from microsoft_agents.hosting.core.http import HttpResponse


@pytest.mark.asyncio
async def test_authorize_request_returns_500_when_config_is_missing():
    with patch(
        "microsoft_agents.hosting.core.authorization.jwt._authorize_request.JwtTokenValidator"
    ) as validator_cls:
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
    claims = ClaimsIdentity({}, False, authentication_type="Anonymous")
    validator = MagicMock()
    validator.get_anonymous_claims.return_value = claims

    with patch(
        "microsoft_agents.hosting.core.authorization.jwt._authorize_request.JwtTokenValidator",
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
    claims = ClaimsIdentity({"aud": "app-id"}, True)
    validator = MagicMock()
    validator.validate_token = AsyncMock(return_value=claims)

    with patch(
        "microsoft_agents.hosting.core.authorization.jwt._authorize_request.JwtTokenValidator",
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

    with patch(
        "microsoft_agents.hosting.core.authorization.jwt._authorize_request.JwtTokenValidator",
        return_value=validator,
    ):
        result = await _authorize_request(
            "Bearer token-value", AgentAuthConfiguration()
        )

    assert isinstance(result, HttpResponse)
    assert result.status_code == 401
    assert result.body == {"error": "Invalid token or authentication failed."}
    validator.validate_token.assert_awaited_once_with("token-value")
