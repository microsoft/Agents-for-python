from os import environ
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AuthTypes
from microsoft_agents.authentication.msal import MsalConnectionManager


class TestMsalConnectionManager:
    """
    Test suite for the Msal Connection Manager
    """

    def test_msal_connection_manager(self):
        mock_environ = {
            **environ,
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "test-tenant-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "test-client-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "test-client-secret-SERVICE_CONNECTION",
            "CONNECTIONS__MCS__SETTINGS__TENANTID": "test-tenant-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTID": "test-client-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTSECRET": "test-client-secret-MCS",
        }

        config = load_configuration_from_env(mock_environ)
        connection_manager = MsalConnectionManager(**config)
        for key in connection_manager._connections:
            auth = connection_manager.get_connection(key)._msal_configuration
            assert auth.AUTH_TYPE == AuthTypes.client_secret
            assert auth.CLIENT_ID == f"test-client-id-{key}"
            assert auth.TENANT_ID == f"test-tenant-id-{key}"
            assert auth.CLIENT_SECRET == f"test-client-secret-{key}"
            assert auth.ISSUERS == [
                "https://api.botframework.com",
                f"https://sts.windows.net/test-tenant-id-{key}/",
                f"https://login.microsoftonline.com/test-tenant-id-{key}/v2.0",
            ]
