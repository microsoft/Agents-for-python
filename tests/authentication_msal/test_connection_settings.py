# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.authentication.msal import (
    MsalAuth,
    MsalConnectionManager,
    MsalConnectionSettings,
)
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AuthTypes,
    ClaimsIdentity,
)


@pytest.mark.parametrize(
    "auth_type, field",
    [
        (AuthTypes.certificate, "CERT_PFX_FILE"),
        (AuthTypes.federated_credentials, "FEDERATED_CLIENT_ID"),
        (AuthTypes.workload_identity, "FEDERATED_TOKEN_FILE"),
    ],
)
def test_required_credentials_are_validated(auth_type, field):
    with pytest.raises(ValueError, match=field):
        MsalConnectionSettings.from_mapping(auth_type=auth_type)


def test_msal_settings_bind_aliases_and_round_trip_legacy_fields_without_mutation():
    legacy = AgentAuthConfiguration(
        client_id="client",
        tenant_id="tenant",
        client_secret="secret",
        authority="https://login.microsoftonline.com",
        scopes=["scope"],
        ALT_BLUEPRINT_NAME="blueprint",
        REGIONALAUTHORITY="westus",
        custom_option="value",
    )
    settings = MsalConnectionSettings._from_agent_auth_config(legacy)
    before = dict(settings.extras)
    restored = settings._to_agent_auth_config()
    assert settings.client_id == restored.CLIENT_ID == "client"
    assert settings.client_secret == restored.CLIENT_SECRET == "secret"
    assert settings.azure_region == restored.AZURE_REGION == "westus"
    assert (
        settings.alternate_blueprint_connection_name
        == restored.ALT_BLUEPRINT_ID
        == "blueprint"
    )
    assert restored.provider_settings["custom_option"] == "value"
    assert settings.extras == before
    assert "_connections" not in settings.extras


@pytest.mark.parametrize("bound", [False, True])
def test_provider_accepts_configuration_or_bound_settings_and_builds_certificate_client(
    mocker, bound
):
    settings = MsalConnectionSettings.from_mapping(
        {
            "SETTINGS": {
                "CLIENTID": "client",
                "TENANTID": "tenant",
                "AUTHTYPE": AuthTypes.certificate,
                "CERTPFXFILE": "certificate.pfx",
                "SENDX5C": "true",
                "REGIONALAUTHORITY": "westus",
            }
        }
    )
    config = (
        settings
        if bound
        else Configuration(
            settings={
                "client_id": "client",
                "tenant_id": "tenant",
                "auth_type": AuthTypes.certificate,
                "cert_pfx_file": "certificate.pfx",
                "send_x5c": "true",
                "azure_region": "westus",
            }
        )
    )
    factory = mocker.patch(
        "microsoft_agents.authentication.msal.msal_auth.ConfidentialClientApplication"
    )
    auth = MsalAuth(config)
    auth._create_client_application()
    assert auth.config.client_id == "client"
    assert factory.call_args.kwargs["client_credential"] == {
        "private_key_pfx_path": "certificate.pfx",
        "public_certificate": True,
    }
    assert factory.call_args.kwargs["azure_region"] == "westus"
    assert auth.configuration.CLIENT_ID == "client"
    assert auth.get_token_credential()._provider is auth


def test_msal_connection_manager_configuration_routes_and_exposes_typed_settings():
    manager = MsalConnectionManager(
        config=Configuration(
            connections={
                "SERVICE_CONNECTION": {"settings": {"client_id": "service"}},
                "MCS": {"settings": {"client_id": "mcs", "tenant_id": "tenant"}},
            },
            connections_map=[{"audience": "mcs", "connection": "MCS"}],
        )
    )
    provider = manager.get_token_provider(
        ClaimsIdentity({"aud": "MCS"}), "https://example.com"
    )
    assert provider is manager.get_connection("MCS")
    assert isinstance(provider.config, MsalConnectionSettings)
    assert provider.config.client_id == "mcs"
