# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.authentication.msal.connection_settings import (
    MsalConnectionSettings,
)
from microsoft_agents.hosting.core import AgentAuthConfiguration, AuthTypes


@pytest.mark.parametrize("wrapper", [None, "SETTINGS", "settings"])
def test_provider_binds_msal_settings_from_configuration(wrapper):
    values = {
        "CLIENTID": "client",
        "CLIENTSECRET": "secret",
        "TENANTID": "tenant",
        "AUTHORITYENDPOINT": "https://authority",
        "SENDX5C": "false",
        "AZUREREGION": "westus",
        "SCOPES": "first second",
        "CUSTOM": {"enabled": True},
    }
    root = Configuration({wrapper: values} if wrapper else values)

    settings = MsalAuth(root).config

    assert isinstance(settings, MsalConnectionSettings)
    assert settings.client_id == "client"
    assert settings.client_secret == "secret"
    assert settings.tenant_id == "tenant"
    assert settings.authority == "https://authority"
    assert settings.send_x5c is False
    assert settings.azure_region == "westus"
    assert settings.scopes == ["first", "second"]
    assert settings.extras["CUSTOM"] == {"enabled": True}
    assert "CLIENTSECRET" not in settings.extras


def test_provider_reuses_bound_settings():
    settings = MsalConnectionSettings(client_id="client")

    assert MsalAuth(settings).config is settings


def test_bound_send_x5c_defaults_to_false():
    assert MsalConnectionSettings.from_mapping({}).send_x5c is False


@pytest.mark.parametrize(
    "auth_type, key",
    [
        (AuthTypes.certificate, "cert_pfx_file"),
        (AuthTypes.federated_credentials, "federated_client_id"),
        (AuthTypes.workload_identity, "federated_token_file"),
    ],
)
def test_binding_validates_required_credentials(auth_type, key):
    with pytest.raises(ValueError, match=key.upper()):
        MsalConnectionSettings.from_mapping(auth_type=auth_type)

    settings = MsalConnectionSettings.from_mapping(
        {"auth_type": auth_type, key: "configured"}
    )

    assert getattr(settings, key) == "configured"


def test_regional_authority_remains_an_alias_with_azure_region_precedence():
    fallback = MsalConnectionSettings.from_mapping({"REGIONALAUTHORITY": "eastus"})
    preferred = MsalConnectionSettings.from_mapping(
        {"AZUREREGION": "westus", "REGIONALAUTHORITY": "eastus"}
    )

    assert fallback.azure_region == "eastus"
    assert preferred.azure_region == "westus"


def test_legacy_provider_configuration_is_supported_with_explicit_warnings():
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        legacy = AgentAuthConfiguration(
            client_id="legacy-client", client_secret="secret", tenant_id="tenant"
        )
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        auth = MsalAuth(legacy)

    assert auth.config.client_id == "legacy-client"
    assert auth.config.client_secret == "secret"
    with pytest.warns(DeprecationWarning, match="deprecated configuration"):
        assert auth.configuration is legacy


def test_new_settings_provide_a_lazy_cached_legacy_view():
    auth = MsalAuth(MsalConnectionSettings(client_id="client", send_x5c=True))

    with pytest.warns(DeprecationWarning, match="deprecated"):
        first = auth.configuration
    with pytest.warns(DeprecationWarning, match="deprecated configuration"):
        second = auth.configuration

    assert isinstance(first, AgentAuthConfiguration)
    assert first is second
    assert first.CLIENT_ID == "client"
    assert first.SEND_X5C is True
