# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core.authorization.jwt import JwtTokenValidator

from . import _helpers


@pytest.mark.asyncio
async def test_real_token_helper_retains_application_configuration(monkeypatch):
    env = {
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "test-app-id",
        "TOKEN_VALIDATION__AUDIENCES__0": "test-audience",
    }
    monkeypatch.setattr(_helpers, "dotenv_values", lambda path: env)
    received = []

    def generate_token(config):
        received.append(config)
        return "test-token"

    monkeypatch.setattr(_helpers, "generate_token_from_config", generate_token)

    token, config = await _helpers.acquire_real_service_connection_token()

    assert token == "test-token"
    assert received == [config]
    assert config["CONNECTIONS"]["SERVICE_CONNECTION"]["SETTINGS"]["CLIENTID"] == (
        "test-app-id"
    )
    assert JwtTokenValidator(config).config.audiences == ["test-audience"]


def test_invalid_audience_override_preserves_connections_and_original_policy():
    config = Configuration(
        {
            "CONNECTIONS": {
                "SERVICE_CONNECTION": {
                    "SETTINGS": {"CLIENTID": "test-app-id", "TENANTID": "test-tenant"}
                }
            },
            "TOKEN_VALIDATION": {
                "AUDIENCES": ["test-audience"],
                "ANONYMOUS_ALLOWED": True,
                "TENANT_ID": "policy-tenant",
            },
        }
    )

    invalid_config = _helpers.auth_config_with_invalid_audience(config)
    policy = JwtTokenValidator(invalid_config).config
    original_policy = JwtTokenValidator(config).config

    assert policy.validate_audience("invalid-audience")
    assert not policy.validate_audience("test-audience")
    assert not policy.validate_audience("test-app-id")
    assert not policy.anonymous_allowed
    assert policy.tenant_id == "policy-tenant"
    assert invalid_config["CONNECTIONS"] == config["CONNECTIONS"]
    assert original_policy.audiences == ["test-audience"]
    assert original_policy.anonymous_allowed
