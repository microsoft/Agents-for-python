import pytest

from microsoft_agents.hosting.core import AuthHandler, AuthHandlerConfig
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config import Configuration

from tests._common.data import (
    DEFAULT_TEST_VALUES,
    NON_AGENTIC_TEST_ENV_DICT,
    AGENTIC_TEST_ENV_DICT,
)

DEFAULTS = DEFAULT_TEST_VALUES()
ENV_DICT = NON_AGENTIC_TEST_ENV_DICT()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


class TestAuthHandler:
    @pytest.mark.parametrize("from_mapping", [False, True])
    def test_indexed_environment_scopes_are_bound_without_mutation(self, from_mapping):
        config = load_configuration_from_env(
            {
                "AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__graph__SETTINGS__SCOPES__2": "Mail.Read",
                "AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__graph__SETTINGS__SCOPES__0": "User.Read",
            }
        )
        settings = config["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"]["graph"][
            "SETTINGS"
        ]
        scopes = settings["SCOPES"]

        handler = (
            AuthHandlerConfig.from_config(settings)
            if from_mapping
            else AuthHandler("graph", **settings)
        )

        assert handler.scopes == ["User.Read", "Mail.Read"]
        assert settings["SCOPES"] is scopes
        assert scopes == ["User.Read", "Mail.Read"]

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

    def test_legacy_constructor_warns_and_preserves_positional_arguments(self):
        with pytest.warns(DeprecationWarning, match="AuthHandler is deprecated"):
            handler = AuthHandler(
                "graph",
                "Sign in",
                "Continue",
                "bot-connection",
                "obo-connection",
                "AgenticUserAuthorization",
                ["User.Read"],
                ALT_BLUEPRINT_NAME="blueprint",
            )

        assert handler == AuthHandler(
            name="graph",
            title="Sign in",
            text="Continue",
            abs_oauth_connection_name="bot-connection",
            obo_connection_name="obo-connection",
            auth_type="AgenticUserAuthorization",
            scopes=["User.Read"],
            ALT_BLUEPRINT_NAME="blueprint",
        )


class TestAuthHandlerConfig:
    @pytest.mark.parametrize("from_configuration", [False, True])
    @pytest.mark.parametrize(
        "scopes",
        ["User.Read, Mail.Read\tFiles.Read", ["User.Read", "Mail.Read", "Files.Read"]],
    )
    def test_normalizes_environment_settings(self, scopes, from_configuration):
        settings = {
            "NAME": "graph",
            "TITLE": "Sign in",
            "TEXT": "Continue",
            "AZUREBOTOAUTHCONNECTIONNAME": "bot-connection",
            "OBOCONNECTIONNAME": "obo-connection",
            "TYPE": "AgenticUserAuthorization",
            "SCOPES": scopes,
            "ALT_BLUEPRINT_NAME": "blueprint",
        }
        handler = (
            AuthHandlerConfig.from_config(Configuration(settings))
            if from_configuration
            else AuthHandlerConfig.from_config(settings)
        )

        assert handler == AuthHandlerConfig(
            name="graph",
            title="Sign in",
            text="Continue",
            abs_oauth_connection_name="bot-connection",
            obo_connection_name="obo-connection",
            auth_type="agenticuserauthorization",
            scopes=["User.Read", "Mail.Read", "Files.Read"],
            _alt_blueprint_name="blueprint",
        )

    def test_from_mapping_applies_optional_defaults(self):
        handler = AuthHandlerConfig.from_config({"name": "graph"})

        assert handler == AuthHandlerConfig(
            name="graph",
            title="",
            text="",
            abs_oauth_connection_name="",
            obo_connection_name="",
            auth_type="userauthorization",
        )

    @pytest.mark.parametrize(
        "settings",
        [
            {
                "name": "graph",
                "abs_oauth_connection_name": "bot-connection",
                "obo_connection_name": "obo-connection",
                "auth_type": "ConnectorUserAuthorization",
            },
            {
                "name": "graph",
                "azurebotoauthconnectionname": "bot-connection",
                "oboconnectionname": "obo-connection",
                "type": "ConnectorUserAuthorization",
            },
        ],
        ids=["snake-case", "lowercase-environment"],
    )
    def test_from_mapping_accepts_different_key_styles(self, settings):
        handler = AuthHandlerConfig.from_config(settings)

        assert handler == AuthHandlerConfig(
            name="graph",
            title="",
            text="",
            abs_oauth_connection_name="bot-connection",
            obo_connection_name="obo-connection",
            auth_type="connectoruserauthorization",
        )
