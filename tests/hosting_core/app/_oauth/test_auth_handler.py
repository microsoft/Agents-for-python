from contextlib import nullcontext

import pytest

from microsoft_agents.hosting.core import (
    AuthHandler,
    AuthHandlerSettings,
    MemoryStorage,
)
from microsoft_agents.hosting.core.app.oauth import (
    AgenticUserAuthorization,
    ConnectorUserAuthorization,
    _UserAuthorization,
)

from tests._common.data import (
    DEFAULT_TEST_VALUES,
    NON_AGENTIC_TEST_ENV_DICT,
    AGENTIC_TEST_ENV_DICT,
)

DEFAULTS = DEFAULT_TEST_VALUES()
ENV_DICT = NON_AGENTIC_TEST_ENV_DICT()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


class TestAuthHandlerSettings:
    def test_default_auth_type(self):
        assert AuthHandlerSettings().auth_type == "userauthorization"

    def test_configuration_aliases(self):
        settings = AuthHandlerSettings(
            NAME="SSO",
            TYPE="AgenticUserAuthorization",
            AZUREBOTOAUTHCONNECTIONNAME="sso",
            OBOCONNECTIONNAME="obo",
            SCOPES="User.Read Mail.Read",
        )

        assert settings.name == "SSO"
        assert settings.auth_type == "agenticuserauthorization"
        assert settings.abs_oauth_connection_name == "sso"
        assert settings.obo_connection_name == "obo"
        assert settings.scopes == ["User.Read", "Mail.Read"]

        copied = AuthHandlerSettings(**settings._to_dict())
        assert copied._to_dict() == settings._to_dict()

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
        auth_handler = AuthHandlerSettings(DEFAULTS.auth_handler_id, **auth_setting)
        assert auth_handler.name == DEFAULTS.auth_handler_id
        assert auth_handler.title == DEFAULTS.auth_handler_title
        assert auth_handler.text == DEFAULTS.auth_handler_text
        assert auth_handler.obo_connection_name == DEFAULTS.obo_connection_name
        assert (
            auth_handler.abs_oauth_connection_name == DEFAULTS.abs_oauth_connection_name
        )

    def test_init_agentic(self, agentic_auth_setting):
        auth_handler = AuthHandlerSettings(
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

    @pytest.mark.parametrize("scopes", [[], ["User.Read"], ["User.Read", "Mail.Read"]])
    def test_settings_round_trip(self, scopes):
        settings = AuthHandlerSettings(
            name="SSO",
            title="Chosen title",
            TITLE="Fallback title",
            scopes=scopes,
            SCOPES=" ".join(scopes),
            ALT_BLUEPRINT_NAME="blueprint",
            CUSTOM_SETTING="custom",
        )

        copied = AuthHandlerSettings(**settings._to_dict())

        assert copied.name == "SSO"
        assert copied.title == "Chosen title"
        assert copied.scopes == scopes
        assert copied.scopes is not settings.scopes
        assert copied._alt_blueprint_name == "blueprint"
        assert copied.kwargs["custom_setting"] == "custom"

    def test_legacy_auth_handler(self, auth_setting):
        with pytest.warns(DeprecationWarning, match="AuthHandler is deprecated"):
            legacy = AuthHandler(DEFAULTS.auth_handler_id, **auth_setting)

        settings = AuthHandlerSettings(DEFAULTS.auth_handler_id, **auth_setting)
        assert isinstance(legacy, AuthHandlerSettings)
        assert legacy._to_dict() == settings._to_dict()


class TestAuthorizationHandlerSettings:
    @pytest.fixture(
        params=[
            _UserAuthorization,
            AgenticUserAuthorization,
            ConnectorUserAuthorization,
        ]
    )
    def handler_type(self, request):
        return request.param

    @pytest.fixture
    def configuration(self):
        return {
            "NAME": "SSO",
            "TITLE": "Sign in",
            "TEXT": "Please sign in",
            "AZUREBOTOAUTHCONNECTIONNAME": "sso",
            "OBOCONNECTIONNAME": "obo",
            "TYPE": "AgenticUserAuthorization",
            "SCOPES": "User.Read Mail.Read",
            "ALT_BLUEPRINT_NAME": "blueprint",
            "CUSTOM_SETTING": "custom",
        }

    @pytest.fixture
    def settings(self, configuration):
        return AuthHandlerSettings(**configuration)

    @pytest.mark.parametrize("settings_kind", ["dictionary", "object"])
    def test_init_with_settings(
        self, mocker, handler_type, configuration, settings, settings_kind
    ):
        storage = MemoryStorage()
        connections = mocker.Mock()
        source = configuration if settings_kind == "dictionary" else settings

        handler = handler_type(storage, connections, settings=source)

        assert handler._storage is storage
        assert handler._connection_manager is connections
        assert handler._id == "SSO"
        assert handler._handler._to_dict() == settings._to_dict()
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]
        if isinstance(handler, AgenticUserAuthorization):
            assert handler._alt_blueprint_name == "blueprint"

    @pytest.mark.parametrize("settings_kind", ["dictionary", "object"])
    def test_settings_take_precedence(
        self, mocker, handler_type, configuration, settings, settings_kind
    ):
        source = configuration if settings_kind == "dictionary" else settings

        handler = handler_type(
            MemoryStorage(),
            mocker.Mock(),
            settings=source,
            title="New title",
            text="New text",
            scopes=["Files.Read"],
            abs_oauth_connection_name="new-sso",
            obo_connection_name="new-obo",
            auth_type="ConnectorUserAuthorization",
            alt_blueprint_name="new-blueprint",
            CUSTOM_SETTING="other",
        )

        assert handler._handler.title == "Sign in"
        assert handler._handler.text == "Please sign in"
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]
        assert handler._handler.abs_oauth_connection_name == "sso"
        assert handler._handler.obo_connection_name == "obo"
        assert handler._handler.auth_type == "agenticuserauthorization"
        assert handler._handler._alt_blueprint_name == "blueprint"
        assert handler._handler.kwargs["custom_setting"] == "custom"
        assert settings.title == "Sign in"
        assert settings.scopes == ["User.Read", "Mail.Read"]
        assert configuration["TITLE"] == "Sign in"
        assert configuration["SCOPES"] == "User.Read Mail.Read"

    @pytest.mark.parametrize(
        "source_kind",
        ["dictionary", "object", "deprecated_dictionary", "deprecated_object"],
    )
    def test_empty_arguments_preserve_settings(
        self, mocker, handler_type, configuration, settings, source_kind
    ):
        source = configuration if "dictionary" in source_kind else settings
        argument = "settings"
        if source_kind == "deprecated_dictionary":
            argument = "auth_handler_settings"
        elif source_kind == "deprecated_object":
            argument = "auth_handler"

        warning = (
            pytest.warns(DeprecationWarning, match="Please use settings instead")
            if source_kind.startswith("deprecated")
            else nullcontext()
        )
        with warning:
            handler = handler_type(
                MemoryStorage(),
                mocker.Mock(),
                **{argument: source},
                title="",
                text="",
                abs_oauth_connection_name="",
                obo_connection_name="",
                scopes=[],
            )

        assert handler._handler.title == "Sign in"
        assert handler._handler.text == "Please sign in"
        assert handler._handler.abs_oauth_connection_name == "sso"
        assert handler._handler.obo_connection_name == "obo"
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]
        assert settings.obo_connection_name == "obo"
        assert settings.scopes == ["User.Read", "Mail.Read"]
        assert configuration["OBOCONNECTIONNAME"] == "obo"
        assert configuration["SCOPES"] == "User.Read Mail.Read"

    @pytest.mark.parametrize("settings_kind", ["dictionary", "object"])
    @pytest.mark.parametrize("empty_value", [None, ""])
    def test_other_arguments_fill_empty_settings(
        self, mocker, handler_type, configuration, settings_kind, empty_value
    ):
        for key in [
            "TITLE",
            "TEXT",
            "AZUREBOTOAUTHCONNECTIONNAME",
            "OBOCONNECTIONNAME",
            "ALT_BLUEPRINT_NAME",
        ]:
            configuration[key] = empty_value
        configuration["SCOPES"] = [] if empty_value == "" else None
        source = (
            configuration
            if settings_kind == "dictionary"
            else AuthHandlerSettings(**configuration)
        )

        handler = handler_type(
            MemoryStorage(),
            mocker.Mock(),
            settings=source,
            title="Fallback title",
            text="Fallback text",
            abs_oauth_connection_name="fallback-sso",
            obo_connection_name="fallback-obo",
            scopes=["Files.Read"],
            alt_blueprint_name="fallback-blueprint",
            OTHER_SETTING="other",
        )

        assert handler._handler.title == "Fallback title"
        assert handler._handler.text == "Fallback text"
        assert handler._handler.abs_oauth_connection_name == "fallback-sso"
        assert handler._handler.obo_connection_name == "fallback-obo"
        assert handler._handler.scopes == ["Files.Read"]
        assert handler._handler._alt_blueprint_name == "fallback-blueprint"
        assert handler._handler.kwargs["custom_setting"] == "custom"
        assert handler._handler.kwargs["other_setting"] == "other"

    @pytest.mark.parametrize("argument", ["settings", "auth_handler"])
    def test_cleared_settings_survive_reconstruction(
        self, mocker, handler_type, settings, argument
    ):
        settings.abs_oauth_connection_name = ""
        settings.obo_connection_name = ""
        settings.scopes = []

        warning = (
            pytest.warns(DeprecationWarning, match="Please use settings instead")
            if argument == "auth_handler"
            else nullcontext()
        )
        with warning:
            handler = handler_type(
                MemoryStorage(), mocker.Mock(), **{argument: settings}
            )

        assert handler._handler.abs_oauth_connection_name == ""
        assert handler._handler.obo_connection_name == ""
        assert handler._handler.scopes == []

    @pytest.mark.parametrize("argument", ["auth_handler", "auth_handler_settings"])
    def test_legacy_keyword_arguments(
        self, mocker, handler_type, configuration, settings, argument
    ):
        source = settings if argument == "auth_handler" else configuration

        with pytest.warns(DeprecationWarning, match="Please use settings instead"):
            handler = handler_type(MemoryStorage(), mocker.Mock(), **{argument: source})

        assert handler._id == "SSO"
        assert handler._handler._to_dict() == settings._to_dict()
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]

    @pytest.mark.parametrize("argument", ["positional", "auth_handler"])
    def test_legacy_auth_handler_instance(
        self, mocker, handler_type, configuration, argument
    ):
        with pytest.warns(DeprecationWarning, match="AuthHandler is deprecated"):
            legacy = AuthHandler(**configuration)

        if argument == "positional":
            handler = handler_type(MemoryStorage(), mocker.Mock(), legacy)
        else:
            with pytest.warns(DeprecationWarning, match="Please use settings instead"):
                handler = handler_type(
                    MemoryStorage(), mocker.Mock(), auth_handler=legacy
                )

        assert handler._id == "SSO"
        assert handler._handler._to_dict() == legacy._to_dict()
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]

    def test_legacy_dictionary_with_explicit_id(
        self, mocker, handler_type, configuration
    ):
        configuration.pop("NAME")

        with pytest.warns(DeprecationWarning, match="Please use settings instead"):
            handler = handler_type(
                MemoryStorage(),
                mocker.Mock(),
                auth_handler_settings=configuration,
                auth_handler_id="legacy-id",
            )

        assert handler._id == "legacy-id"
        assert handler._handler.abs_oauth_connection_name == "sso"
        assert handler._handler.obo_connection_name == "obo"
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]
