# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration, load_configuration_from_env
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
    assert "_configured_issuers" not in settings.extras


@pytest.mark.parametrize(
    "auth_type, credential",
    [
        (AuthTypes.certificate, {"cert_pfx_file": "certificate.pfx"}),
        (AuthTypes.federated_credentials, {"federated_client_id": "identity"}),
        (AuthTypes.workload_identity, {"federated_token_file": "token-file"}),
    ],
)
def test_settings_bind_required_credentials_from_configuration(auth_type, credential):
    settings = MsalConnectionSettings.from_mapping(auth_type=auth_type, **credential)
    auth = MsalAuth(settings)

    assert auth.config.auth_type == auth_type
    assert getattr(auth.config, next(iter(credential))) == next(
        iter(credential.values())
    )


@pytest.mark.parametrize(
    "values, field, expected",
    [
        ({"SENDX5C": "false"}, "send_x5c", False),
        ({"SENDX5C": "true"}, "send_x5c", True),
        ({"AZUREREGION": "eastus"}, "azure_region", "eastus"),
        ({"REGIONALAUTHORITY": "westus"}, "azure_region", "westus"),
        (
            {"AZUREREGION": "eastus", "REGIONALAUTHORITY": "westus"},
            "azure_region",
            "eastus",
        ),
        (
            {"AUTHORITY": "https://primary", "AUTHORITYENDPOINT": "https://secondary"},
            "authority",
            "https://primary",
        ),
        ({"AUTHORITYENDPOINT": "https://authority"}, "authority", "https://authority"),
        (
            {"ALT_BLUEPRINT_NAME": "legacy", "ALTERNATEBLUEPRINTCONNECTIONNAME": "new"},
            "alternate_blueprint_connection_name",
            "legacy",
        ),
        (
            {"IDPMRESOURCE": "https://resource/.default"},
            "idpm_resource",
            "https://resource/.default",
        ),
    ],
)
def test_settings_bind_legacy_aliases_and_precedence(values, field, expected):
    settings = MsalConnectionSettings.from_mapping(values)

    assert getattr(settings, field) == expected


def test_msal_settings_bind_environment_fields_without_exposing_credentials_in_extras():
    config = load_configuration_from_env(
        {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "client",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "tenant",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "test-secret",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SENDX5C": "false",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SCOPES__2": "scope2",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SCOPES__0": "scope1",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CUSTOM_OPTION": "custom",
        }
    )
    manager = MsalConnectionManager(config=config)
    settings = manager.get_default_connection().config

    assert (settings.client_id, settings.tenant_id, settings.client_secret) == (
        "client",
        "tenant",
        "test-secret",
    )
    assert settings.send_x5c is False
    assert settings.scopes == ["scope1", "scope2"]
    assert settings.extras["CUSTOM_OPTION"] == "custom"
    assert "CLIENTSECRET" not in settings.extras
    assert "test-secret" not in repr(settings)


def test_legacy_msal_provider_and_compatibility_view_emit_deprecations():
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration is deprecated"):
        legacy = AgentAuthConfiguration(client_id="client")
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration is deprecated"):
        auth = MsalAuth(legacy)
    with pytest.warns(
        DeprecationWarning, match="Accessing the deprecated configuration"
    ):
        assert auth.configuration is legacy


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
