# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import time

import pytest
from azure.core.credentials import AccessToken
from dotenv import dotenv_values

from microsoft_agents.authentication.msal import MsalTokenCredential
from microsoft_agents.hosting.core import AgentAuthConfiguration

from tests.utils.config import REAL_SERVICE_CONNECTION_ENV_VARS
from tests.utils.pytest import skip_if_no_var

_CLIENT_ID_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"
_CLIENT_SECRET_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET"
_TENANT_ID_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID"
_BOT_FRAMEWORK_SCOPE = "https://api.botframework.com/.default"
_ENVIRONMENT = {**dotenv_values(".env"), **os.environ}

pytestmark = skip_if_no_var(
    *REAL_SERVICE_CONNECTION_ENV_VARS,
    environ=_ENVIRONMENT,
)


@pytest.fixture
def auth_config() -> AgentAuthConfiguration:
    return AgentAuthConfiguration(
        client_id=_ENVIRONMENT[_CLIENT_ID_ENV_VAR],
        client_secret=_ENVIRONMENT[_CLIENT_SECRET_ENV_VAR],
        tenant_id=_ENVIRONMENT[_TENANT_ID_ENV_VAR],
    )


@pytest.mark.asyncio
async def test_msal_token_credential_acquires_token(
    auth_config: AgentAuthConfiguration,
):
    credential = MsalTokenCredential(auth_config)

    token = await credential.get_token(_BOT_FRAMEWORK_SCOPE)

    assert isinstance(token, AccessToken)
    assert token.token
    assert token.expires_on > time.time()
