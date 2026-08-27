# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from azure.core.credentials import AccessToken

from microsoft_agents.authentication.msal import MsalTokenCredential
from microsoft_agents.hosting.core import AgentAuthConfiguration

_FIRST_SCOPE = "https://api.botframework.com/.default"
_SECOND_SCOPE = "https://graph.microsoft.com/.default"
_MSAL_AUTH_PATH = "microsoft_agents.authentication.msal.msal_token_credential.MsalAuth"


@pytest.fixture
def auth_config() -> AgentAuthConfiguration:
    return AgentAuthConfiguration(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
    )


@pytest.mark.asyncio
async def test_get_token_returns_access_token_and_forwards_scopes(
    mocker,
    auth_config: AgentAuthConfiguration,
):
    msal_auth_class = mocker.patch(_MSAL_AUTH_PATH)
    msal_auth = msal_auth_class.return_value
    expected_token = AccessToken("access-token", 1234567890)
    msal_auth._get_access_token = mocker.AsyncMock(return_value=expected_token)
    credential = MsalTokenCredential(auth_config)

    token = await credential.get_token(_FIRST_SCOPE, _SECOND_SCOPE)

    assert token is expected_token
    msal_auth_class.assert_called_once_with(auth_config)
    msal_auth._get_access_token.assert_awaited_once_with(
        _FIRST_SCOPE,
        [_FIRST_SCOPE, _SECOND_SCOPE],
    )


@pytest.mark.asyncio
async def test_get_token_requires_at_least_one_scope(
    mocker,
    auth_config: AgentAuthConfiguration,
):
    msal_auth_class = mocker.patch(_MSAL_AUTH_PATH)
    credential = MsalTokenCredential(auth_config)

    with pytest.raises(ValueError, match="At least one scope must be provided"):
        await credential.get_token()

    msal_auth_class.assert_not_called()


@pytest.mark.asyncio
async def test_get_token_propagates_msal_auth_error(
    mocker,
    auth_config: AgentAuthConfiguration,
):
    msal_auth = mocker.patch(_MSAL_AUTH_PATH).return_value
    msal_auth._get_access_token = mocker.AsyncMock(
        side_effect=RuntimeError("token acquisition failed")
    )
    credential = MsalTokenCredential(auth_config)

    with pytest.raises(RuntimeError, match="token acquisition failed"):
        await credential.get_token(_FIRST_SCOPE)
