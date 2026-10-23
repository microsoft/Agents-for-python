# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core.authorization.jwt.jwt_connection_settings import (
    JwtConnectionSettings,
)
from microsoft_agents.hosting.core.authorization.jwt.jwt_token_validator import (
    _validate_issuer,
)


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


@pytest.mark.parametrize("key", ["issuers", "ISSUERS"])
def test_explicit_issuers_override_computed_defaults(key):
    issuers = ["https://custom-issuer.example.com/"]

    settings = JwtConnectionSettings.from_mapping({key: issuers, "tenant_id": "tenant"})

    assert settings.issuers == issuers


@pytest.mark.parametrize(
    "value",
    [
        ["https://first.example.com/", "https://second.example.com/"],
        "https://first.example.com/ https://second.example.com/",
        "https://first.example.com/, https://second.example.com/",
    ],
)
def test_explicit_issuer_formats_validate_each_configured_issuer(value):
    settings = JwtConnectionSettings.from_mapping(
        {"ISSUERS": value, "VALIDATE_ISSUER": True}
    )

    assert settings.issuers == [
        "https://first.example.com/",
        "https://second.example.com/",
    ]
    for issuer in settings.issuers:
        _validate_issuer(issuer, settings)


def test_indexed_issuers_from_environment_remain_supported():
    config = load_configuration_from_env(
        {
            "SETTINGS__ISSUERS__0": "https://first.example.com/",
            "SETTINGS__ISSUERS__1": "https://second.example.com/",
        }
    )

    settings = JwtConnectionSettings.from_configuration(config)

    assert settings.issuers == [
        "https://first.example.com/",
        "https://second.example.com/",
    ]


@pytest.mark.parametrize(
    "raw, expected", [(False, False), (True, True), ("false", False), ("true", True)]
)
def test_boolean_policy_fields_are_bound_explicitly(raw, expected):
    settings = JwtConnectionSettings.from_mapping(
        {"VALIDATE_ISSUER": raw, "ANONYMOUS_ALLOWED": raw}
    )

    assert settings.validate_issuer is expected
    assert settings.anonymous_allowed is expected


def test_boolean_policy_defaults_remain_false():
    settings = JwtConnectionSettings.from_mapping({})

    assert settings.validate_issuer is False
    assert settings.anonymous_allowed is False
