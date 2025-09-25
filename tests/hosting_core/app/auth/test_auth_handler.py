import pytest

from microsoft_agents.hosting.core import AuthHandler

from tests._common.data import TEST_DEFAULTS, TEST_ENV_DICT

DEFAULTS = TEST_DEFAULTS()
ENV_DICT = TEST_ENV_DICT()


class TestAuthHandler:
    @pytest.fixture
    def auth_setting(self):
        return ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][
            DEFAULTS.auth_handler_id
        ]["SETTINGS"]

    def test_init(self, auth_setting):
        auth_handler = AuthHandler(DEFAULTS.auth_handler_id, **auth_setting)
        assert auth_handler.name == DEFAULTS.auth_handler_id
        assert auth_handler.title == DEFAULTS.auth_handler_title
        assert auth_handler.text == DEFAULTS.auth_handler_text
        assert auth_handler.obo_connection_name == DEFAULTS.obo_connection_name
        assert (
            auth_handler.abs_oauth_connection_name == DEFAULTS.abs_oauth_connection_name
        )
