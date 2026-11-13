# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration, _resolve
from microsoft_agents.hosting.core.authorization.connections import (
    ConnectionSettingsBase,
)
from microsoft_agents.hosting.core.authorization.jwt import JwtConnectionSettings
from microsoft_agents.hosting.core import AgentAuthConfiguration


def test_legacy_binding_preserves_explicit_issuers_without_internal_provider_extras():
    legacy = AgentAuthConfiguration(
        client_id="client",
        issuers=["https://custom.example/"],
        validate_issuer=True,
        anonymous_allowed=True,
        custom_option="value",
    )
    original_connections = legacy._connections
    settings = JwtConnectionSettings._from_agent_auth_config(legacy)

    assert settings.issuers == ["https://custom.example/"]
    assert settings.validate_issuer is True
    assert settings.anonymous_allowed is True
    assert settings.extras["custom_option"] == "value"
    assert "_connections" not in settings.extras
    assert "_configured_issuers" not in settings.extras
    assert legacy._connections is original_connections
    assert legacy.ISSUERS == ["https://custom.example/"]


@pytest.mark.parametrize(
    "tenant_id, authority, effective_tenant, cloud",
    [
        (None, None, "common", "com"),
        ("tenant", None, "tenant", "com"),
        ("tenant", "https://login.microsoftonline.us", "tenant", "us"),
        ("tenant", "https://login.microsoftonline.com/common", "common", "com"),
        ("common", "https://login.microsoftonline.com/concrete", "concrete", "com"),
    ],
)
def test_default_issuers_use_effective_tenant_and_cloud(
    tenant_id, authority, effective_tenant, cloud
):
    settings = JwtConnectionSettings.from_config(
        dict(tenant_id=tenant_id, authority=authority)
    )
    assert settings.issuers == [
        f"https://api.botframework.{cloud}",
        f"https://sts.windows.net/{effective_tenant}/",
        f"https://login.microsoftonline.{cloud}/{effective_tenant}/v2.0",
    ]


@pytest.mark.parametrize(
    "value",
    [
        ["https://first.example.com/", "https://second.example.com/"],
        "https://first.example.com/ https://second.example.com/",
        "https://first.example.com/, https://second.example.com/",
    ],
)
def test_explicit_issuers_override_defaults(value):
    settings = JwtConnectionSettings.from_config(
        {"ISSUERS": value, "VALIDATE_ISSUER": "true", "ANONYMOUS_ALLOWED": "false"}
    )
    assert settings.issuers == [
        "https://first.example.com/",
        "https://second.example.com/",
    ]
    assert settings.validate_issuer is True
    assert settings.anonymous_allowed is False


def test_indexed_issuers_from_environment():
    config = Configuration(
        _resolve(
            {
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ISSUERS__10": "https://third.example.com/",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ISSUERS__2": "https://second.example.com/",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ISSUERS__0": "https://first.example.com/",
            }
        )
    )
    connection = config.get_section(["CONNECTIONS", "SERVICE_CONNECTION"])
    assert connection["SETTINGS"]["ISSUERS"] == [
        "https://first.example.com/",
        "https://second.example.com/",
        "https://third.example.com/",
    ]
    assert JwtConnectionSettings.from_config(connection).issuers == [
        "https://first.example.com/",
        "https://second.example.com/",
        "https://third.example.com/",
    ]


def test_unresolved_indexed_issuers_require_normalization():
    with pytest.raises(ValueError, match="ISSUERS"):
        JwtConnectionSettings.from_config(
            {"ISSUERS": {"0": "https://first.example.com/"}}
        )


def test_base_settings_bind_aliases_scopes_and_provider_extras():
    settings = ConnectionSettingsBase.from_config(
        {
            "SETTINGS": {
                "CLIENTID": "client",
                "TENANT_ID": "tenant",
                "AUTHORITYENDPOINT": "https://login.microsoftonline.us",
                "ALT_BLUEPRINT_NAME": "blueprint",
                "SCOPES": "scope1 scope2",
                "provider_option": "value",
                "extras": {"fallback_option": "fallback"},
            }
        }
    )
    assert settings.client_id == "client"
    assert settings.tenant_id == "tenant"
    assert settings.authority == "https://login.microsoftonline.us"
    assert settings.alternate_blueprint_connection_name == "blueprint"
    assert settings.scopes == ["scope1", "scope2"]
    assert settings.extras["provider_option"] == "value"
    assert settings.extras["fallback_option"] == "fallback"
