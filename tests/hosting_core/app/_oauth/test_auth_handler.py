import pytest

from microsoft_agents.hosting.core import AuthHandler

from tests._common.data import (
    DEFAULT_TEST_VALUES,
    NON_AGENTIC_TEST_ENV_DICT,
    AGENTIC_TEST_ENV_DICT,
)

DEFAULTS = DEFAULT_TEST_VALUES()
ENV_DICT = NON_AGENTIC_TEST_ENV_DICT()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


class TestAuthHandler:
    @pytest.fixture
    def auth_setting(self):
        return ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][
            DEFAULTS.auth_handler_id
        ]["SETTINGS"]

    @pytest.fixture
    def agentic_auth_setting(self):
        return AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][
            DEFAULTS.agentic_auth_handler_id
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

    def test_init_agentic(self, agentic_auth_setting):
        auth_handler = AuthHandler(
            DEFAULTS.agentic_auth_handler_id, **agentic_auth_setting
        )
        assert auth_handler.name == DEFAULTS.agentic_auth_handler_id
        assert auth_handler.title == DEFAULTS.agentic_auth_handler_title
        assert auth_handler.text == DEFAULTS.agentic_auth_handler_text
        assert auth_handler.obo_connection_name == DEFAULTS.agentic_obo_connection_name
        assert auth_handler.scopes == ["user.Read", "Mail.Read"]
        assert (
            auth_handler.abs_oauth_connection_name
            == DEFAULTS.agentic_abs_oauth_connection_name
        )
