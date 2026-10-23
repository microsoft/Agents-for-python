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

    @pytest.mark.parametrize("key_style", ["upper", "lower", "snake"])
    def test_configuration_aliases(self, key_style):
        configuration = {
            "NAME": "SSO",
            "TYPE": "AgenticUserAuthorization",
            "AZUREBOTOAUTHCONNECTIONNAME": "sso",
            "OBOCONNECTIONNAME": "obo",
            "SCOPES": "User.Read Mail.Read",
        }
        if key_style != "upper":
            configuration = {k.lower(): v for k, v in configuration.items()}
        if key_style == "snake":
            configuration["auth_type"] = configuration.pop("type")
            configuration["abs_oauth_connection_name"] = configuration.pop(
                "azurebotoauthconnectionname"
            )
            configuration["obo_connection_name"] = configuration.pop(
                "oboconnectionname"
            )
            configuration["scopes"] = ["User.Read", "Mail.Read"]
        settings = AuthHandlerSettings(**configuration)

        assert settings.name == "SSO"
        assert settings.auth_type == "agenticuserauthorization"
        assert settings.abs_oauth_connection_name == "sso"
        assert settings.obo_connection_name == "obo"
        assert settings.scopes == ["User.Read", "Mail.Read"]

        copied = AuthHandlerSettings(**settings._to_dict())
        assert copied._to_dict() == settings._to_dict()

    @pytest.mark.parametrize("scopes_key", ["scopes", "SCOPES"])
    def test_scopes_are_copied(self, scopes_key):
        scopes = ["User.Read"]
        settings = AuthHandlerSettings(**{scopes_key: scopes})

        scopes.append("Mail.Read")

        assert settings.scopes == ["User.Read"]

    def test_kwargs_returns_a_copy(self):
        settings = AuthHandlerSettings(CUSTOM_SETTING="custom")
        extras = settings.kwargs

        extras["custom_setting"] = "changed"
        extras["new_setting"] = "new"

        assert settings.kwargs == {"custom_setting": "custom"}

    @pytest.mark.parametrize("empty_value", [None, ""])
    def test_empty_arguments_use_configuration(self, empty_value):
        settings = AuthHandlerSettings(
            name=empty_value,
            title=empty_value,
            text=empty_value,
            abs_oauth_connection_name=empty_value,
            obo_connection_name=empty_value,
            auth_type=empty_value,
            scopes=None if empty_value is None else [],
            NAME="SSO",
            TITLE="Sign in",
            TEXT="Please sign in",
            AZUREBOTOAUTHCONNECTIONNAME="sso",
            OBOCONNECTIONNAME="obo",
            TYPE="AgenticUserAuthorization",
            SCOPES="User.Read Mail.Read",
            ALT_BLUEPRINT_NAME="blueprint",
            CUSTOM_SETTING="custom",
        )

        assert settings.name == "SSO"
        assert settings.title == "Sign in"
        assert settings.text == "Please sign in"
        assert settings.abs_oauth_connection_name == "sso"
        assert settings.obo_connection_name == "obo"
        assert settings.auth_type == "agenticuserauthorization"
        assert settings.scopes == ["User.Read", "Mail.Read"]
        assert settings._alt_blueprint_name == "blueprint"
        assert settings.kwargs == {"custom_setting": "custom"}

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
        if settings_kind == "object":
            assert handler._handler is settings
        if isinstance(handler, AgenticUserAuthorization):
            assert handler._alt_blueprint_name == "blueprint"

    @pytest.mark.parametrize(
        "settings_kind",
        ["dictionary", "object", "deprecated_dictionary", "deprecated_object"],
    )
    def test_handler_kwargs_do_not_modify_settings(
        self, mocker, handler_type, configuration, settings, settings_kind
    ):
        source = configuration if "dictionary" in settings_kind else settings
        argument = {
            "deprecated_dictionary": "auth_handler_settings",
            "deprecated_object": "auth_handler",
        }.get(settings_kind, "settings")

        warning = (
            pytest.warns(DeprecationWarning, match="Please use settings instead")
            if settings_kind.startswith("deprecated")
            else nullcontext()
        )
        with warning:
            handler = handler_type(
                MemoryStorage(),
                mocker.Mock(),
                **{argument: source},
                title="New title",
                text="New text",
                scopes=["Files.Read"],
                abs_oauth_connection_name="new-sso",
                obo_connection_name="new-obo",
                auth_type="ConnectorUserAuthorization",
                alt_blueprint_name="new-blueprint",
                CUSTOM_SETTING="other",
                OTHER_SETTING="ignored",
            )

        assert handler._handler.title == "Sign in"
        assert handler._handler.text == "Please sign in"
        assert handler._handler.scopes == ["User.Read", "Mail.Read"]
        assert handler._handler.abs_oauth_connection_name == "sso"
        assert handler._handler.obo_connection_name == "obo"
        assert handler._handler.auth_type == "agenticuserauthorization"
        assert handler._handler._alt_blueprint_name == "blueprint"
        assert handler._handler.kwargs["custom_setting"] == "custom"
        assert "other_setting" not in handler._handler.kwargs
        assert settings.title == "Sign in"
        assert settings.scopes == ["User.Read", "Mail.Read"]
        assert configuration["TITLE"] == "Sign in"
        assert configuration["SCOPES"] == "User.Read Mail.Read"

    @pytest.mark.parametrize(
        "settings_kind",
        ["dictionary", "object", "deprecated_dictionary", "deprecated_object"],
    )
    def test_missing_optional_settings(self, mocker, handler_type, settings_kind):
        configuration = {"NAME": "SSO"}
        source = (
            configuration
            if "dictionary" in settings_kind
            else AuthHandlerSettings(**configuration)
        )
        argument = {
            "deprecated_dictionary": "auth_handler_settings",
            "deprecated_object": "auth_handler",
        }.get(settings_kind, "settings")

        warning = (
            pytest.warns(DeprecationWarning, match="Please use settings instead")
            if settings_kind.startswith("deprecated")
            else nullcontext()
        )
        with warning:
            handler = handler_type(
                MemoryStorage(),
                mocker.Mock(),
                **{argument: source},
            )

        assert handler._id == "SSO"
        assert handler._handler.title == ""
        assert handler._handler.text == ""
        assert handler._handler.abs_oauth_connection_name == ""
        assert handler._handler.obo_connection_name == ""
        assert handler._handler.auth_type == "userauthorization"
        assert handler._handler.scopes == []
        assert handler._handler._alt_blueprint_name is None
        assert handler._handler.kwargs == {}

    @pytest.mark.parametrize("argument", ["settings", "auth_handler"])
    def test_modified_settings_object_is_preserved(
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

        assert handler._handler is settings
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
        assert handler._handler is legacy
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
