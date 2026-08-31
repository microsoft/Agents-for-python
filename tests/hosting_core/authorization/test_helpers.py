# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime

import pytest
from azure.core.credentials import AccessToken

from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core.authorization._helpers import (
    _CallableTokenCredential,
    _access_token_from_token_response,
)


@pytest.mark.parametrize(
    "expiration, expected",
    [
        (None, 0),
        ("2030-01-01T00:00:00Z", 1893456000),
        ("2030-01-01T00:00:00", 1893456000),
        ("2030-01-01T02:00:00+02:00", 1893456000),
    ],
)
def test_access_token_from_token_response_expiration(expiration, expected):
    response = TokenResponse(token="token", expiration=expiration)

    token = _access_token_from_token_response(response)

    assert token == AccessToken("token", expected)


def test_access_token_from_token_response_rejects_missing_token():
    with pytest.raises(ValueError, match="Failed to retrieve token"):
        _access_token_from_token_response(TokenResponse())


def test_access_token_from_token_response_rejects_invalid_expiration():
    with pytest.raises(ValueError):
        _access_token_from_token_response(
            TokenResponse(token="token", expiration="not-a-date")
        )


@pytest.mark.asyncio
async def test_callable_token_credential_returns_access_token_unchanged(mocker):
    expected = AccessToken("token", 123)
    retriever = mocker.AsyncMock(return_value=expected)
    credential = _CallableTokenCredential(retriever)

    token = await credential.get_token("scope", claims="claims")

    assert token is expected
    retriever.assert_awaited_once_with("scope", claims="claims")


@pytest.mark.asyncio
async def test_callable_token_credential_converts_token_response():
    async def retrieve_token(*scopes: str, **kwargs):
        return TokenResponse(
            token="token",
            expiration="2030-01-01T02:00:00+02:00",
        )

    credential = _CallableTokenCredential(retrieve_token)

    token = await credential.get_token("scope")

    assert token == AccessToken("token", 1893456000)


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [None, TokenResponse()])
async def test_callable_token_credential_rejects_missing_token(result):
    async def retrieve_token(*scopes: str, **kwargs):
        return result

    credential = _CallableTokenCredential(retrieve_token)

    with pytest.raises(ValueError, match="Failed to retrieve token"):
        await credential.get_token("scope")
