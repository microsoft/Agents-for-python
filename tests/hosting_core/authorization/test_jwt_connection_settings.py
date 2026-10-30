# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration, _resolve
from microsoft_agents.hosting.core.authorization.connection_settings_base import (
    ConnectionSettingsBase,
)
from microsoft_agents.hosting.core.authorization.jwt import JwtConnectionSettings


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
    settings = JwtConnectionSettings.from_mapping(
        tenant_id=tenant_id, authority=authority
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
    settings = JwtConnectionSettings.from_mapping(
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
    connection = config.get_section("CONNECTIONS::SERVICE_CONNECTION")
    assert connection["SETTINGS"]["ISSUERS"] == [
        "https://first.example.com/",
        "https://second.example.com/",
        "https://third.example.com/",
    ]
    assert JwtConnectionSettings.from_configuration(connection).issuers == [
        "https://first.example.com/",
        "https://second.example.com/",
        "https://third.example.com/",
    ]


def test_unresolved_indexed_issuers_require_normalization():
    with pytest.raises(ValueError, match="ISSUERS"):
        JwtConnectionSettings.from_mapping(
            {"ISSUERS": {"0": "https://first.example.com/"}}
        )


def test_base_settings_bind_aliases_scopes_and_provider_extras():
    settings = ConnectionSettingsBase.from_mapping(
        {
            "SETTINGS": {
                "CLIENTID": "client",
                "TENANT_ID": "tenant",
                "AUTHORITYENDPOINT": "https://login.microsoftonline.us",
                "ALT_BLUEPRINT_ID": "blueprint",
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
