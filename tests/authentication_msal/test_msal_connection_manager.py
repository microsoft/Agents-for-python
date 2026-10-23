import pytest

from copy import deepcopy

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AuthTypes, ClaimsIdentity
from microsoft_agents.authentication.msal import MsalConnectionManager

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
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "test-tenant-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "test-client-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "test-client-secret-SERVICE_CONNECTION",
            "CONNECTIONS__MCS__SETTINGS__TENANTID": "test-tenant-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTID": "test-client-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTSECRET": "test-client-secret-MCS",
        }

        config = load_configuration_from_env(mock_environ)
        connection_manager = MsalConnectionManager(config=config)
        for key in connection_manager._connections:
            auth = connection_manager.get_connection(key).config
            assert auth.auth_type == AuthTypes.client_secret
            assert auth.client_id == f"test-client-id-{key}"
            assert auth.tenant_id == f"test-tenant-id-{key}"
            assert auth.client_secret == f"test-client-secret-{key}"

    # TODO -> test other init paths

    @pytest.mark.parametrize(
        "claims_identity, service_url",
        [
            [None, ""],
            [None, None],
            [None, "agentic"],
            [ClaimsIdentity(claims={}), None],
            [ClaimsIdentity(claims={}), ""],
            [ClaimsIdentity(claims={}), "https://example.com"],
            [ClaimsIdentity(claims={"aud": "api://misc"}), ""],
        ],
    )
    def test_get_token_provider_errors(self, claims_identity, service_url):
        connection_manager = MsalConnectionManager(config=Configuration(ENV_CONFIG))
        with pytest.raises(ValueError):
            connection_manager.get_token_provider(claims_identity, service_url)

    def test_get_token_provider_no_map(self, config):
        del config["CONNECTIONSMAP"]
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={"aud": "api://misc"})
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://example.com"
        )
        assert token_provider == connection_manager.get_default_connection()

    def test_get_token_provider_aud_match(self, config):
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={"aud": "api://misc"})
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://example.com"
        )
        assert token_provider == connection_manager.get_connection("MISC")

    def test_get_token_provider_aud_and_service_url_match(self, config):
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={"aud": "api://service"})
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://service.com/api"
        )
        assert token_provider == connection_manager.get_connection("SERVICE_CONNECTION")

    def test_get_token_provider_service_url_wildcard_star(self, config):
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={"aud": "api://misc"})
        token_provider = connection_manager.get_token_provider(
            claims_identity, "https://service.com/api"
        )
        assert token_provider == connection_manager.get_connection("MISC")

    def test_get_token_provider_service_url_wildcard_empty(self, config):
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={"aud": "api://misc_other"})
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
        connection_manager = MsalConnectionManager(config=Configuration(config))
        claims_identity = ClaimsIdentity(claims={})
        token_provider = connection_manager.get_token_provider(
            claims_identity, service_url
        )
        assert token_provider == connection_manager.get_connection(expected_connection)
