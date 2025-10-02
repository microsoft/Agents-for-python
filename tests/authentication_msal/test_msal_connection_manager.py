import pytest

from copy import deepcopy

from os import environ
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AuthTypes, ClaimsIdentity
from microsoft_agents.authentication.msal import MsalConnectionManager

from tests._common.create_env_var_dict import create_env_var_dict

from ._data import ENV_CONFIG


class TestMsalConnectionManager:
    """
    Test suite for the Msal Connection Manager
    """

    @pytest.fixture
    def config(self):
        return deepcopy(ENV_CONFIG)

    def test_init_from_config(self):
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

    # TODO -> test other init paths

    @pytest.mark.parametrize(
        "claims_identity, service_url",
        [
            [None, ""],
            [None, None],
            [None, "agentic"],
            [ClaimsIdentity(claims={}, is_authenticated=False), None],
            [ClaimsIdentity(claims={}, is_authenticated=False), ""],
            [ClaimsIdentity(claims={}, is_authenticated=False), "https://example.com"],
            [ClaimsIdentity(claims={"aud": "api://misc"}, is_authenticated=False), ""],
        ],
    )
    def test_get_token_provider_errors(self, claims_identity, service_url):
        connection_manager = MsalConnectionManager(**ENV_CONFIG)
        with pytest.raises(ValueError):
            connection_manager.get_token_provider(claims_identity, service_url)

    def test_get_token_provider_no_map(self, config):
        del config["CONNECTIONSMAP"]
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(
            claims={"aud": "api://misc"}, is_authenticated=True
        )
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://example.com"
        )
        assert token_provider == connection_manager.get_default_connection()

    def test_get_token_provider_aud_match(self, config):
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(
            claims={"aud": "api://misc"}, is_authenticated=True
        )
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://example.com"
        )
        assert token_provider == connection_manager.get_connection("MISC")

    def test_get_token_provider_aud_and_service_url_match(self, config):
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(
            claims={"aud": "api://service"}, is_authenticated=True
        )
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://service.com/api"
        )
        assert token_provider == connection_manager.get_connection("SERVICE_CONNECTION")

    def test_get_token_provider_service_url_wildcard_star(self, config):
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(
            claims={"aud": "api://misc"}, is_authenticated=False
        )
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://service.com/api"
        )
        assert token_provider == connection_manager.get_connection("MISC")

    def test_get_token_provider_service_url_wildcard_empty(self, config):
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(
            claims={"aud": "api://misc_other"}, is_authenticated=False
        )
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://service.com/api"
        )
        assert token_provider == connection_manager.get_connection("MISC")

    @pytest.mark.parametrize(
        "service_url, expected_connection",
        [
            ["agentic", "AGENTIC"],
            ["https://microsoft.com/api", "MISC"],
            ["https://microsoft.com/some-url", "MISC"],
            ["https://microsoft.com/", "MISC"],
        ],
    )
    def test_get_token_provider_service_url_match(
        self, config, service_url, expected_connection
    ):
        connection_manager = MsalConnectionManager(**config)
        claims_identity = ClaimsIdentity(claims={}, is_authenticated=False)
        token_provider = connection_manager.get_token_provider(
            claims_identity, service_url
        )
        assert token_provider == connection_manager.get_connection(expected_connection)
