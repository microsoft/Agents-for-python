from os import environ
from typing import Dict
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AgentAuthConfiguration, AuthTypes


class TestAuthorizationConfiguration:
    """
    Unit tests to validate Authorization Configuration cases
    """

    def test_auth_configuration_basic(self):
        # test AgentAuthConfiguration with manual insertion of fields
        auth_config = AgentAuthConfiguration(
            auth_type=AuthTypes.client_secret,
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            client_secret="test-client-secret",
            cert_pfx_file="test-cert.pfx",
            connection_name="test-connection",
            authority="https://login.microsoftonline.com",
            scopes=["test-scope-1", "test-scope-2"],
        )

        assert auth_config.AUTH_TYPE == AuthTypes.client_secret
        assert auth_config.TENANT_ID == "test-tenant-id"
        assert auth_config.CLIENT_ID == "test-client-id"
        assert auth_config.CLIENT_SECRET == "test-client-secret"
        assert auth_config.CERT_PFX_FILE == "test-cert.pfx"
        assert auth_config.CONNECTION_NAME == "test-connection"
        assert auth_config.AUTHORITY == "https://login.microsoftonline.com"
        assert auth_config.SCOPES == ["test-scope-1", "test-scope-2"]
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            f"https://sts.windows.net/test-tenant-id/",
            f"https://login.microsoftonline.com/test-tenant-id/v2.0",
        ]

    def test_load_configuration_from_env(self):
        # test load_configuration_from_env, passed to AgentAuthConfiguration
        mock_environ = {
            **environ,
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "test-tenant-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "test-client-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "test-client-secret-SERVICE_CONNECTION",
            "CONNECTIONS__MCS__SETTINGS__TENANTID": "test-tenant-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTID": "test-client-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTSECRET": "test-client-secret-MCS",
        }

        mock_config = load_configuration_from_env(mock_environ)

        raw_configurations: Dict[str, Dict] = mock_config.get("CONNECTIONS", {})

        for name, settings in raw_configurations.items():
            auth_config = AgentAuthConfiguration(**settings["SETTINGS"])
            assert auth_config.AUTH_TYPE == AuthTypes.client_secret
            assert auth_config.CLIENT_ID == f"test-client-id-{name}"
            assert auth_config.TENANT_ID == f"test-tenant-id-{name}"
            assert auth_config.CLIENT_SECRET == f"test-client-secret-{name}"
            assert auth_config.ISSUERS == [
                "https://api.botframework.com",
                f"https://sts.windows.net/test-tenant-id-{name}/",
                f"https://login.microsoftonline.com/test-tenant-id-{name}/v2.0",
            ]

    def test_empty_settings(self):
        auth_config = AgentAuthConfiguration()
        assert auth_config.AUTH_TYPE == AuthTypes.client_secret
        assert auth_config.TENANT_ID is None
        assert auth_config.CLIENT_ID is None
        assert auth_config.CLIENT_SECRET is None
        assert auth_config.CERT_PFX_FILE is None
        assert auth_config.FEDERATED_CLIENT_ID is None
        assert auth_config.CONNECTION_NAME is None
        assert auth_config.AUTHORITY is None
        assert auth_config.SCOPES is None
        assert auth_config.AZURE_REGION is None

    def test_azure_region_from_parameter(self):
        auth_config = AgentAuthConfiguration(azure_region="westus")
        assert auth_config.AZURE_REGION == "westus"

    def test_azure_region_from_kwargs(self):
        auth_config = AgentAuthConfiguration(AZUREREGION="eastus")
        assert auth_config.AZURE_REGION == "eastus"

    def test_azure_region_legacy_regional_authority_fallback(self):
        # When AZUREREGION is not provided, fall back to the legacy
        # RegionalAuthority configuration key.
        auth_config = AgentAuthConfiguration(REGIONALAUTHORITY="westeurope")
        assert auth_config.AZURE_REGION == "westeurope"

    def test_azure_region_prefers_azure_region_over_legacy(self):
        auth_config = AgentAuthConfiguration(
            AZUREREGION="eastus", REGIONALAUTHORITY="westeurope"
        )
        assert auth_config.AZURE_REGION == "eastus"

    def test_idpm_resource_defaults_none(self):
        auth_config = AgentAuthConfiguration()
        assert auth_config.IDPM_RESOURCE is None

    def test_idpm_resource_from_parameter(self):
        auth_config = AgentAuthConfiguration(
            auth_type=AuthTypes.identity_proxy_manager,
            client_id="test-client-id",
            idpm_resource="https://custom-resource/.default",
        )
        assert auth_config.AUTH_TYPE == AuthTypes.identity_proxy_manager
        assert auth_config.IDPM_RESOURCE == "https://custom-resource/.default"

    def test_idpm_resource_from_kwargs(self):
        auth_config = AgentAuthConfiguration(
            IDPMRESOURCE="https://custom-resource/.default"
        )
        assert auth_config.IDPM_RESOURCE == "https://custom-resource/.default"
