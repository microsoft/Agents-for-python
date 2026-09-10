# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import os
import time

import jwt
import pytest
from azure.core.credentials import AccessToken
from dotenv import dotenv_values
from jwt import PyJWKClient

from microsoft_agents.authentication.msal import MsalTokenCredential
from microsoft_agents.hosting.core import AgentAuthConfiguration

from tests.utils.config import REAL_SERVICE_CONNECTION_ENV_VARS
from tests.utils.pytest import skip_if_no_var

_CLIENT_ID_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"
_CLIENT_SECRET_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET"
_TENANT_ID_ENV_VAR = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID"
_BOT_FRAMEWORK_RESOURCE = "https://api.botframework.com"
_BOT_FRAMEWORK_SCOPE = f"{_BOT_FRAMEWORK_RESOURCE}/.default"
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
async def test_msal_token_credential_acquires_valid_token(
    auth_config: AgentAuthConfiguration,
):
    credential = MsalTokenCredential(auth_config)

    token = await credential.get_token(_BOT_FRAMEWORK_SCOPE)

    assert isinstance(token, AccessToken)
    assert token.token
    assert token.expires_on > time.time()

    unverified_claims = jwt.decode(
        token.token,
        options={"verify_signature": False},
    )
    token_version = unverified_claims.get("ver")
    assert token_version in ("1.0", "2.0")

    tenant_id = auth_config.TENANT_ID
    issuer = (
        f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        if token_version == "2.0"
        else f"https://sts.windows.net/{tenant_id}/"
    )
    jwks_client = PyJWKClient(
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    )
    signing_key = await asyncio.to_thread(
        jwks_client.get_signing_key_from_jwt,
        token.token,
    )

    claims = jwt.decode(
        token.token,
        signing_key.key,
        algorithms=["RS256"],
        audience=_BOT_FRAMEWORK_RESOURCE,
        issuer=issuer,
    )

    assert claims["tid"] == tenant_id
    assert abs(claims["exp"] - token.expires_on) <= 5
    client_id_claim = "azp" if token_version == "2.0" else "appid"
    assert claims[client_id_claim] == auth_config.CLIENT_ID
