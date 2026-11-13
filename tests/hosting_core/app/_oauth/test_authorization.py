import pytest
import jwt
import warnings

from typing import Optional

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    SignInConstants,
    TokenResponse,
)
from microsoft_agents.activity.config import Configuration

from microsoft_agents.hosting.core.app.oauth import (
    _SignInResponse,
    _SignInState,
    _UserAuthorization,
    Authorization,
    AgenticUserAuthorization,
    ConnectorUserAuthorization,
)
from microsoft_agents.hosting.core.app.oauth.authorization_config import (
    AuthorizationConfig,
)

from microsoft_agents.hosting.core._oauth import _FlowStateTag

from microsoft_agents.hosting.core import (
    AuthHandler,
    AuthHandlerConfig,
    MemoryStorage,
)

from tests._common.storage.utils import StorageBaseline

# test constants
from tests._common.data import (
    FLOW_TEST_DATA,
    AUTH_TEST_DATA,
    STORAGE_TEST_DATA,
    DEFAULT_TEST_VALUES,
    NON_AGENTIC_TEST_ENV_DICT,
    AGENTIC_TEST_ENV_DICT,
)
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import (
    TestingConnectionManager as MockConnectionManager,
    mock_class_UserAuthorization,
    mock_class_AgenticUserAuthorization,
    mock_class_Authorization,
)

from ._common import create_testing_TurnContext, create_testing_Activity
from tests._common import create_configuration

DEFAULTS = DEFAULT_TEST_VALUES()
FLOW_DATA = FLOW_TEST_DATA()
STORAGE_DATA = STORAGE_TEST_DATA()
ENV_DICT = NON_AGENTIC_TEST_ENV_DICT()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


def make_jwt(token: str = DEFAULTS.token, aud="api://default"):
    if aud:
        return jwt.encode({"aud": aud}, token, algorithm="HS256")
    else:
        return jwt.encode({}, token, algorithm="HS256")


def mock_variants(mocker, sign_in_return=None, get_refreshed_token_return=None):
    mock_class_UserAuthorization(
        mocker,
        sign_in_return=sign_in_return,
        get_refreshed_token_return=get_refreshed_token_return,
    )
    mock_class_AgenticUserAuthorization(
        mocker,
        sign_in_return=sign_in_return,
        get_refreshed_token_return=get_refreshed_token_return,
    )


def sign_in_state_eq(a: Optional[_SignInState], b: Optional[_SignInState]) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return (
        a.active_handler_id == b.active_handler_id
        and a.continuation_activity == b.continuation_activity
    )


def create_turn_state(context, token_cache: dict):

    d = {**context.turn_state}
    d.update(
        {
            Authorization._cache_key(context, k): TokenResponse(token=v)
            for k, v in token_cache.items()
        }
    )
    return d


def copy_sign_in_state(state: _SignInState) -> _SignInState:
    return _SignInState(
        active_handler_id=state.active_handler_id,
        continuation_activity=(
            state.continuation_activity.model_copy()
            if state.continuation_activity
            else None
        ),
    )


class TestEnv(FlowStateFixtures):
    def setup_method(self):
        self.TurnContext = create_testing_TurnContext
        self.ConnectionManager = lambda mocker: MockConnectionManager()

    @pytest.fixture
    def context(self, mocker):
        return self.TurnContext(mocker)

    @pytest.fixture
    def activity(self):
        return create_testing_Activity()

    @pytest.fixture
    def baseline_storage(self):
        return StorageBaseline(STORAGE_TEST_DATA().dict)

    @pytest.fixture
    def storage(self):
        return MemoryStorage(STORAGE_DATA.get_init_data())

    @pytest.fixture
    def connection_manager(self, mocker):
        return self.ConnectionManager(mocker)

    @pytest.fixture
    def auth_handlers(self):
        return AUTH_TEST_DATA().auth_handlers

    @pytest.fixture
    def authorization(self, connection_manager, storage):
        return Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)

    @pytest.fixture(params=[ENV_DICT, AGENTIC_ENV_DICT])
    def env_dict(self, request):
        return request.param

    @pytest.fixture(params=[DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id])
    def auth_handler_id(self, request):
        return request.param


class TestAuthorizationSetup(TestEnv):
    @pytest.mark.parametrize(
        "auth_type, handler_class",
        [
            ("UserAuthorization", _UserAuthorization),
            ("AgenticUserAuthorization", AgenticUserAuthorization),
            ("ConnectorUserAuthorization", ConnectorUserAuthorization),
        ],
    )
    def test_init_with_directly_constructed_settings(
        self, connection_manager, storage, auth_type, handler_class
    ):
        settings = AuthHandlerConfig(
            name="graph",
            title="Sign in",
            text="Continue",
            abs_oauth_connection_name="bot-connection",
            obo_connection_name="obo-connection",
            auth_type=auth_type,
            scopes=["User.Read"],
        )

        auth = Authorization(
            storage, connection_manager, auth_handlers={"graph": settings}
        )

        assert isinstance(auth._resolve_handler("graph"), handler_class)

    def test_handler_list_replaces_configured_handlers(
        self, connection_manager, storage
    ):
        graph = AuthHandlerConfig(name="graph", scopes=["User.Read"])
        mail = AuthHandlerConfig(name="mail", scopes=["Mail.Read"])
        config = AuthorizationConfig(
            handlers={"configured": AuthHandlerConfig(name="configured")}
        )

        auth = Authorization(
            storage, connection_manager, auth_handlers=[graph, mail], config=config
        )

        assert list(auth._handlers) == ["graph", "mail"]
        assert auth._resolve_handler("graph")._handler is graph
        assert auth._resolve_handler("mail")._handler is mail
        assert auth._default_handler_id == "graph"

    def test_handler_list_duplicate_names_use_last_definition(
        self, connection_manager, storage
    ):
        first = AuthHandlerConfig(name="graph", scopes=["User.Read"])
        last = AuthHandlerConfig(name="graph", scopes=["Mail.Read"])

        auth = Authorization(storage, connection_manager, auth_handlers=[first, last])

        assert list(auth._handlers) == ["graph"]
        assert auth._resolve_handler("graph")._handler is last

    def test_empty_handler_list_uses_configured_handlers(
        self, connection_manager, storage
    ):
        handler = AuthHandlerConfig(name="graph", scopes=["User.Read"])
        config = AuthorizationConfig(handlers={"graph": handler})

        auth = Authorization(
            storage, connection_manager, auth_handlers=[], config=config
        )

        assert list(auth._handlers) == ["graph"]
        assert auth._resolve_handler("graph")._handler is handler

    @pytest.mark.parametrize(
        "auth_type, handler_class",
        [
            ("UserAuthorization", _UserAuthorization),
            ("AgenticUserAuthorization", AgenticUserAuthorization),
            ("ConnectorUserAuthorization", ConnectorUserAuthorization),
        ],
    )
    @pytest.mark.parametrize("as_mapping", [False, True])
    @pytest.mark.parametrize("positional", [False, True])
    def test_init_with_settings(
        self,
        connection_manager,
        storage,
        auth_type,
        handler_class,
        as_mapping,
        positional,
    ):
        settings = AuthHandlerConfig.from_config(
            {
                "name": "graph",
                "auth_type": auth_type,
                "scopes": ["User.Read"],
                "_alt_blueprint_name": "blueprint",
            }
        )
        value = vars(settings) if as_mapping else settings
        handler = (
            handler_class(storage, connection_manager, value)
            if positional
            else handler_class(storage, connection_manager, config=value)
        )

        assert handler._id == "graph"
        assert handler._handler == settings
        if not as_mapping:
            assert handler._handler is settings
        if isinstance(handler, AgenticUserAuthorization):
            assert handler._alt_blueprint_name == "blueprint"

        auth = Authorization(
            storage, connection_manager, auth_handlers={"graph": settings}
        )
        assert isinstance(auth._resolve_handler("graph"), handler_class)

    @pytest.mark.parametrize(
        "auth_type, handler_class",
        [
            ("UserAuthorization", _UserAuthorization),
            ("AgenticUserAuthorization", AgenticUserAuthorization),
            ("ConnectorUserAuthorization", ConnectorUserAuthorization),
        ],
    )
    @pytest.mark.parametrize(
        "config_argument", ["root", "section", "mapping", "bound", "kwargs"]
    )
    @pytest.mark.parametrize("type_in_settings", [False, True])
    def test_init_from_configuration(
        self,
        connection_manager,
        storage,
        auth_type,
        handler_class,
        config_argument,
        type_in_settings,
    ):
        handler_config = {
            "SETTINGS": {
                "TITLE": "Sign in",
                "TEXT": "Continue",
                "AZUREBOTOAUTHCONNECTIONNAME": "bot-connection",
                "OBOCONNECTIONNAME": "obo-connection",
                "SCOPES": "User.Read, Mail.Read",
                "ALT_BLUEPRINT_NAME": "blueprint",
            }
        }
        if type_in_settings:
            handler_config["SETTINGS"]["TYPE"] = auth_type
        else:
            handler_config["TYPE"] = auth_type
        config = create_configuration(
            {
                "AGENTAPPLICATION": {
                    "USERAUTHORIZATION": {
                        "HANDLERS": {"graph": handler_config},
                        "AUTOSIGNIN": "true",
                    }
                }
            },
            is_root=True,
        )

        if config_argument == "kwargs":
            with pytest.warns(
                DeprecationWarning, match="Passing configuration via kwargs"
            ):
                auth = Authorization(storage, connection_manager, **config)
        else:
            section = config.get_section(["AGENTAPPLICATION", "USERAUTHORIZATION"])
            settings = {
                "root": config,
                "section": section,
                "mapping": dict(section),
                "bound": AuthorizationConfig.from_config(config),
            }[config_argument]
            with warnings.catch_warnings():
                warnings.simplefilter("error", DeprecationWarning)
                auth = Authorization(storage, connection_manager, config=settings)
        handler = auth._resolve_handler("graph")

        assert isinstance(handler, handler_class)
        assert auth._auto_sign_in is True
        assert handler._handler == AuthHandlerConfig(
            name="graph",
            title="Sign in",
            text="Continue",
            abs_oauth_connection_name="bot-connection",
            obo_connection_name="obo-connection",
            auth_type=auth_type.lower(),
            scopes=["User.Read", "Mail.Read"],
            _alt_blueprint_name="blueprint",
        )

    @pytest.mark.parametrize(
        "configured, explicit, expected",
        [
            (False, None, False),
            (False, False, False),
            (False, True, True),
            (True, None, True),
            (True, False, False),
            (True, True, True),
        ],
    )
    def test_auto_sign_in_only_inherits_config_when_unspecified(
        self, connection_manager, storage, configured, explicit, expected
    ):
        auth = Authorization(
            storage,
            connection_manager,
            auto_sign_in=explicit,
            config=Configuration({"auto_sign_in": configured}),
        )

        assert auth._auto_sign_in is expected

    @pytest.mark.parametrize("bound", [False, True])
    def test_explicit_settings_ignore_legacy_kwargs(
        self, connection_manager, storage, caplog, bound
    ):
        scoped = Configuration(
            dict(
                handlers={"graph": {"SETTINGS": {"SCOPES": "User.Read"}}},
                auto_sign_in=False,
            )
        )
        settings = AuthorizationConfig.from_config(scoped) if bound else scoped
        legacy = {
            "AGENTAPPLICATION": {
                "USERAUTHORIZATION": {
                    "AUTOSIGNIN": True,
                    "HANDLERS": {"ignored": {"TYPE": "invalid"}},
                }
            }
        }

        with pytest.warns(DeprecationWarning, match="Passing configuration via kwargs"):
            auth = Authorization(storage, connection_manager, config=settings, **legacy)

        assert list(auth._handlers) == ["graph"]
        assert auth._resolve_handler("graph")._handler.scopes == ["User.Read"]
        assert auth._auto_sign_in is False
        assert "'kwargs' will be ignored in favor of 'config'" in caplog.text

    @pytest.mark.parametrize(
        "settings",
        [
            None,
            create_configuration(dict(unrelated=True), is_root=True),
            Configuration(),
            AuthorizationConfig(),
        ],
        ids=["omitted", "missing-root-section", "empty-section", "bound-defaults"],
    )
    def test_empty_settings_do_not_emit_deprecation_warnings(
        self, connection_manager, storage, settings
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            auth = Authorization(storage, connection_manager, config=settings)

        assert auth._handlers == {}
        assert auth._auto_sign_in is False

    @pytest.mark.parametrize(
        "handler_class",
        [_UserAuthorization, AgenticUserAuthorization, ConnectorUserAuthorization],
    )
    @pytest.mark.parametrize(
        "legacy_argument", ["auth_handler", "auth_handler_settings"]
    )
    def test_legacy_settings_arguments_warn(
        self, connection_manager, storage, legacy_argument, handler_class
    ):
        settings = AuthHandlerConfig.from_config({"name": "graph"})
        value = settings if legacy_argument == "auth_handler" else vars(settings)

        with pytest.warns(
            DeprecationWarning, match="auth_handler and auth_handler_settings"
        ):
            handler = handler_class(
                storage, connection_manager, **{legacy_argument: value}
            )

        assert handler._handler == settings

    def test_init_user_auth(self, connection_manager, storage, env_dict):
        auth = Authorization(storage, connection_manager, **env_dict)
        assert auth._resolve_handler(DEFAULTS.auth_handler_id) is not None
        assert isinstance(
            auth._resolve_handler(DEFAULTS.auth_handler_id), _UserAuthorization
        )

    def test_init_agentic_auth_not_configured(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        with pytest.raises(ValueError):
            auth._resolve_handler(DEFAULTS.agentic_auth_handler_id)

    def test_init_agentic_auth(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)
        assert auth._resolve_handler(DEFAULTS.agentic_auth_handler_id) is not None
        assert isinstance(
            auth._resolve_handler(DEFAULTS.agentic_auth_handler_id),
            AgenticUserAuthorization,
        )

    @pytest.mark.parametrize(
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    def test_resolve_handler(self, connection_manager, storage, auth_handler_id):
        auth = Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)
        handler_config = AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"][
            "HANDLERS"
        ][auth_handler_id]
        auth._resolve_handler(auth_handler_id) == AuthHandler(
            auth_handler_id, **handler_config
        )

    def test_connection_manager_property(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        assert auth.connection_manager is connection_manager

    def test_sign_in_state_key(self, mocker, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        context = self.TurnContext(mocker)
        key = auth._sign_in_state_key(context)
        assert key == f"auth:_SignInState:{DEFAULTS.channel_id}:{DEFAULTS.user_id}"


class TestAuthorizationUsage(TestEnv):
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_turn_state, final_turn_state, initial_sign_in_state, auth_handler_id",
        [
            [
                {DEFAULTS.auth_handler_id: DEFAULTS.token},
                {},
                None,
                DEFAULTS.auth_handler_id,
            ],
            [
                {DEFAULTS.auth_handler_id: DEFAULTS.token},
                {},
                _SignInState(
                    active_handler_id="some_value_bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJV0E="
                ),
                DEFAULTS.auth_handler_id,
            ],
            [
                {DEFAULTS.agentic_auth_handler_id: DEFAULTS.token},
                {DEFAULTS.agentic_auth_handler_id: DEFAULTS.token},
                None,
                DEFAULTS.auth_handler_id,
            ],
            [
                {
                    DEFAULTS.agentic_auth_handler_id: DEFAULTS.token,
                    DEFAULTS.auth_handler_id: "value",
                },
                {DEFAULTS.auth_handler_id: "value"},
                _SignInState(
                    active_handler_id="some_value_bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJV0E="
                ),
                DEFAULTS.agentic_auth_handler_id,
            ],
        ],
    )
    async def test_sign_out(
        self,
        mocker,
        storage,
        authorization,
        context,
        initial_turn_state,
        final_turn_state,
        initial_sign_in_state,
        auth_handler_id,
    ):
        # setup
        mock_variants(mocker)
        expected_turn_state = create_turn_state(context, final_turn_state)
        context.turn_state = create_turn_state(context, initial_turn_state)
        if initial_sign_in_state:
            await authorization._save_sign_in_state(context, initial_sign_in_state)

        # test
        await authorization.sign_out(context, auth_handler_id)

        # verify
        assert context.turn_state == expected_turn_state
        assert (await authorization._load_sign_in_state(context)) is None
        assert authorization._get_cached_token(context, auth_handler_id) is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_cache, final_cache, auth_handler_id, expected_auth_handler_id, "
        "initial_sign_in_state, final_sign_in_state, sign_in_response",
        [
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                {DEFAULTS.auth_handler_id: "valid_token"},
                DEFAULTS.auth_handler_id,
                DEFAULTS.auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
                None,
                _SignInResponse(
                    token_response=TokenResponse(token="valid_token"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                {
                    DEFAULTS.agentic_auth_handler_id: "valid_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                None,
                DEFAULTS.agentic_auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.agentic_auth_handler_id),
                None,
                _SignInResponse(
                    token_response=TokenResponse(token="valid_token"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                {DEFAULTS.auth_handler_id: "valid_token"},
                DEFAULTS.auth_handler_id,
                DEFAULTS.auth_handler_id,
                None,
                None,
                _SignInResponse(
                    token_response=TokenResponse(token="valid_token"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                {DEFAULTS.auth_handler_id: "valid_token"},
                None,
                DEFAULTS.auth_handler_id,
                None,
                None,
                _SignInResponse(
                    token_response=TokenResponse(token="valid_token"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                {
                    DEFAULTS.agentic_auth_handler_id: "old_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                {
                    DEFAULTS.agentic_auth_handler_id: "valid_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                DEFAULTS.agentic_auth_handler_id,
                DEFAULTS.agentic_auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.agentic_auth_handler_id),
                None,
                _SignInResponse(
                    token_response=TokenResponse(token="valid_token"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                {
                    DEFAULTS.agentic_auth_handler_id: "old_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                {
                    DEFAULTS.agentic_auth_handler_id: "old_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                DEFAULTS.agentic_auth_handler_id,
                DEFAULTS.agentic_auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.agentic_auth_handler_id),
                None,
                _SignInResponse(
                    token_response=TokenResponse(),
                    tag=_FlowStateTag.FAILURE,
                ),
            ],
            [
                {
                    DEFAULTS.agentic_auth_handler_id: "old_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                {
                    DEFAULTS.agentic_auth_handler_id: "old_token",
                    DEFAULTS.auth_handler_id: "old_token",
                },
                None,
                DEFAULTS.auth_handler_id,
                None,
                None,
                _SignInResponse(
                    token_response=TokenResponse(),
                    tag=_FlowStateTag.FAILURE,
                ),
            ],
        ],
    )
    async def test_start_or_continue_sign_in_complete_or_failure(
        self,
        mocker,
        storage,
        authorization,
        context,
        initial_cache,
        final_cache,
        auth_handler_id,
        expected_auth_handler_id,
        initial_sign_in_state,
        final_sign_in_state,
        sign_in_response,
    ):
        # setup
        mock_variants(mocker, sign_in_return=sign_in_response)
        expected_turn_state = create_turn_state(context, final_cache)
        context.turn_state = create_turn_state(context, initial_cache)
        if not initial_sign_in_state:
            await authorization._delete_sign_in_state(context)
        else:
            await authorization._save_sign_in_state(context, initial_sign_in_state)

        # test

        res = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )

        # verify
        assert res.tag == sign_in_response.tag
        assert res.token_response == sign_in_response.token_response

        authorization._resolve_handler(
            expected_auth_handler_id
        )._sign_in.assert_called_once_with(context)
        assert (await authorization._load_sign_in_state(context)) is None
        assert context.turn_state == expected_turn_state

    @pytest.fixture(params=[_FlowStateTag.BEGIN, _FlowStateTag.CONTINUE])
    def pending_tag(self, request):
        return request.param

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_cache, auth_handler_id, expected_auth_handler_id, initial_sign_in_state",
        [
            [
                {DEFAULTS.agentic_auth_handler_id: "old_token"},
                DEFAULTS.auth_handler_id,
                DEFAULTS.auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
            ],
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                None,
                DEFAULTS.agentic_auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.agentic_auth_handler_id),
            ],
            [
                {},
                DEFAULTS.auth_handler_id,
                DEFAULTS.auth_handler_id,
                None,
            ],
            [
                {DEFAULTS.auth_handler_id: "old_token"},
                None,
                DEFAULTS.auth_handler_id,
                None,
            ],
            [
                {},
                DEFAULTS.agentic_auth_handler_id,
                DEFAULTS.auth_handler_id,
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
            ],
        ],
    )
    async def test_start_or_continue_sign_in_pending(
        self,
        mocker,
        storage,
        authorization,
        context,
        initial_cache,
        auth_handler_id,
        expected_auth_handler_id,
        initial_sign_in_state,
        pending_tag,
    ):
        # setup
        mock_variants(mocker, sign_in_return=_SignInResponse(tag=pending_tag))
        expected_turn_state = create_turn_state(context, initial_cache)
        context.turn_state = expected_turn_state
        if not initial_sign_in_state:
            await authorization._delete_sign_in_state(context)
        else:
            await authorization._save_sign_in_state(context, initial_sign_in_state)

        # test

        res = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )

        # verify
        assert res.tag == pending_tag
        assert not res.token_response

        authorization._resolve_handler(
            expected_auth_handler_id
        )._sign_in.assert_called_once_with(context)
        final_sign_in_state = await authorization._load_sign_in_state(context)
        assert final_sign_in_state.continuation_activity == context.activity
        assert final_sign_in_state.active_handler_id == expected_auth_handler_id
        assert context.turn_state == expected_turn_state

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_state, initial_cache, handler_id, expected_handler_id, refresh_token, expected",
        [
            [  # no cached token
                _SignInState(active_handler_id="value"),
                {DEFAULTS.auth_handler_id: "token"},
                DEFAULTS.agentic_auth_handler_id,
                DEFAULTS.agentic_auth_handler_id,
                TokenResponse(),
                TokenResponse(),
            ],
            [  # no cached token and default handler id resolution
                _SignInState(active_handler_id="value"),
                {DEFAULTS.agentic_auth_handler_id: "token"},
                "",
                DEFAULTS.auth_handler_id,
                TokenResponse(),
                TokenResponse(),
            ],
            [  # no cached token pt.2
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
                {DEFAULTS.agentic_auth_handler_id: "token"},
                DEFAULTS.auth_handler_id,
                DEFAULTS.auth_handler_id,
                TokenResponse(),
                TokenResponse(),
            ],
            [  # refreshed, new token
                _SignInState(active_handler_id="value"),
                {DEFAULTS.agentic_auth_handler_id: make_jwt()},
                DEFAULTS.agentic_auth_handler_id,
                DEFAULTS.agentic_auth_handler_id,
                TokenResponse(token=DEFAULTS.token),
                TokenResponse(token=DEFAULTS.token),
            ],
        ],
    )
    async def test_get_token(
        self,
        mocker,
        authorization,
        context,
        storage,
        initial_state,
        initial_cache,
        handler_id,
        expected_handler_id,
        refresh_token,
        expected,
    ):
        # setup
        mock_variants(mocker, get_refreshed_token_return=refresh_token)
        expected_turn_state = create_turn_state(context, initial_cache)
        context.turn_state = expected_turn_state
        if not initial_state:
            await authorization._delete_sign_in_state(context)
        else:
            await authorization._save_sign_in_state(context, initial_state)

        # test
        res = await authorization.get_token(context, handler_id)
        assert res == expected

        if handler_id and refresh_token:
            authorization._resolve_handler(
                expected_handler_id
            ).get_refreshed_token.assert_called_once_with(context, None, None)

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(initial_state, final_state)
        assert context.turn_state == expected_turn_state

    @pytest.mark.asyncio
    async def test_get_token_as_token_credential(self, mocker, authorization, context):
        token_response = TokenResponse(
            token=DEFAULTS.token,
            expiration="2030-01-01T00:00:00Z",
        )
        exchange_token = mocker.patch.object(
            authorization,
            "exchange_token",
            new=mocker.AsyncMock(return_value=token_response),
        )

        credential = authorization.get_token_as_token_credential(
            context,
            auth_handler_id=DEFAULTS.auth_handler_id,
        )
        token = await credential.get_token(
            "scope1",
            "scope2",
            claims="claims",
            tenant_id="tenant",
            enable_cae=True,
        )

        assert token.token == DEFAULTS.token
        exchange_token.assert_awaited_once_with(
            context,
            auth_handler_id=DEFAULTS.auth_handler_id,
            scopes=["scope1", "scope2"],
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_state, initial_cache, handler_id, refreshed, refresh_token",
        [
            [  # no cached token
                None,
                {DEFAULTS.auth_handler_id: "token"},
                DEFAULTS.agentic_auth_handler_id,
                False,
                TokenResponse(),
            ],
            [  # no cached token and default handler id resolution
                None,
                {DEFAULTS.agentic_auth_handler_id: "token"},
                "",
                False,
                TokenResponse(),
            ],
            [  # no cached token pt.2
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
                {DEFAULTS.agentic_auth_handler_id: "token"},
                DEFAULTS.auth_handler_id,
                True,
                TokenResponse(),
            ],
            [  # refreshed, new token
                _SignInState(active_handler_id=DEFAULTS.auth_handler_id),
                {DEFAULTS.agentic_auth_handler_id: DEFAULTS.token},
                DEFAULTS.agentic_auth_handler_id,
                True,
                TokenResponse(token=DEFAULTS.token),
            ],
        ],
    )
    async def test_exchange_token(
        self,
        mocker,
        authorization,
        context,
        storage,
        initial_state,
        initial_cache,
        handler_id,
        refreshed,
        refresh_token,
    ):
        # setup
        mock_variants(mocker, get_refreshed_token_return=refresh_token)
        expected_turn_state = create_turn_state(context, initial_cache)
        context.turn_state = expected_turn_state
        if not initial_state:
            await authorization._delete_sign_in_state(context)
        else:
            await authorization._save_sign_in_state(context, initial_state)

        res = await authorization.exchange_token(
            context,
            auth_handler_id=handler_id,
            exchange_connection="some_connection",
            scopes=["scope1", "scope2"],
        )
        assert res == refresh_token

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(initial_state, final_state)
        if handler_id and refresh_token:
            authorization._resolve_handler(
                handler_id
            ).get_refreshed_token.assert_called_once_with(
                context, "some_connection", ["scope1", "scope2"]
            )

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(initial_state, final_state)
        assert context.turn_state == expected_turn_state

    @pytest.mark.asyncio
    async def test_exchange_token_as_token_credential(
        self, mocker, authorization, context
    ):
        token_response = TokenResponse(
            token=DEFAULTS.token,
            expiration="2030-01-01T00:00:00Z",
        )
        exchange_token = mocker.patch.object(
            authorization,
            "exchange_token",
            new=mocker.AsyncMock(return_value=token_response),
        )

        credential = authorization.exchange_token_as_token_credential(
            context,
            scopes=["configured", "shared"],
            auth_handler_id=DEFAULTS.auth_handler_id,
            exchange_connection="connection",
        )
        token = await credential.get_token(
            "shared",
            "requested",
            claims="claims",
        )

        assert token.token == DEFAULTS.token
        exchange_token.assert_awaited_once_with(
            context,
            scopes=["configured", "shared", "requested"],
            auth_handler_id=DEFAULTS.auth_handler_id,
            exchange_connection="connection",
        )

    @pytest.mark.asyncio
    async def test_on_turn_auth_intercept_no_intercept(
        self, storage, authorization, context
    ):
        await authorization._delete_sign_in_state(context)

        res = await authorization._on_turn_auth_intercept(context, None)

        assert not res.continuation_activity
        assert not res.should_skip_turn
        assert not res.should_replay

        final_state = await authorization._load_sign_in_state(context)

        assert sign_in_state_eq(final_state, None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "sign_in_response",
        [
            _SignInResponse(tag=_FlowStateTag.BEGIN),
            _SignInResponse(tag=_FlowStateTag.CONTINUE),
            _SignInResponse(tag=_FlowStateTag.FAILURE),
        ],
    )
    async def test_on_turn_auth_intercept_with_intercept_incomplete(
        self, mocker, storage, authorization, context, sign_in_response, auth_handler_id
    ):
        mock_class_Authorization(
            mocker, start_or_continue_sign_in_return=sign_in_response
        )

        initial_cache = {"some_handler": "old_token"}
        expected_cache = create_turn_state(context, initial_cache)
        context.turn_state = expected_cache

        initial_state = _SignInState(
            active_handler_id=auth_handler_id,
            continuation_activity=Activity(
                type=ActivityTypes.message, text="old activity"
            ),
        )
        await authorization._save_sign_in_state(
            context, copy_sign_in_state(initial_state)
        )

        res = await authorization._on_turn_auth_intercept(context, auth_handler_id)

        assert not res.continuation_activity
        assert res.should_skip_turn
        assert not res.should_replay

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(final_state, initial_state)
        assert context.turn_state == expected_cache

    @pytest.mark.asyncio
    async def test_on_turn_auth_intercept_with_intercept_complete(
        self, mocker, storage, authorization, context, auth_handler_id
    ):
        mock_class_Authorization(
            mocker,
            start_or_continue_sign_in_return=_SignInResponse(
                tag=_FlowStateTag.COMPLETE
            ),
        )

        initial_cache = {"some_handler": "old_token"}
        expected_cache = create_turn_state(context, initial_cache)
        context.turn_state = expected_cache

        old_activity = Activity(type=ActivityTypes.message, text="old activity")
        initial_state = _SignInState(
            active_handler_id=auth_handler_id, continuation_activity=old_activity
        )
        await authorization._save_sign_in_state(
            context, copy_sign_in_state(initial_state)
        )

        res = await authorization._on_turn_auth_intercept(context, auth_handler_id)

        assert res.continuation_activity == old_activity
        assert res.should_skip_turn
        assert res.should_replay

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(final_state, initial_state)
        assert context.turn_state == expected_cache


class TestTeamsSSOConsentRequired(TestEnv):
    """Tests for the Teams SSO ConsentRequired special case in _start_or_continue_sign_in.

    When a pending signin/tokenExchange invoke arrives on Teams and a continuation_activity
    already exists in the sign-in state, the state must NOT be updated so the original
    activity is preserved for the eventual resume turn.
    """

    @pytest.fixture(params=[_FlowStateTag.BEGIN, _FlowStateTag.CONTINUE])
    def pending_tag(self, request):
        return request.param

    @pytest.mark.asyncio
    async def test_skips_state_update_for_teams_sso_consent_required(
        self, mocker, storage, authorization, pending_tag
    ):
        """All four conditions met → continuation_activity is NOT overwritten."""
        original_continuation = Activity(type=ActivityTypes.message, text="original")
        teams_invoke_activity = Activity(
            type=ActivityTypes.invoke,
            channel_id=Channels.ms_teams,
            from_property={"id": DEFAULTS.user_id},
            name=SignInConstants.token_exchange_operation_name,
        )
        context = create_testing_TurnContext(mocker, activity=teams_invoke_activity)
        initial_state = _SignInState(
            active_handler_id=DEFAULTS.auth_handler_id,
            continuation_activity=original_continuation,
        )
        await authorization._save_sign_in_state(context, initial_state)
        mock_variants(mocker, sign_in_return=_SignInResponse(tag=pending_tag))

        res = await authorization._start_or_continue_sign_in(
            context, None, DEFAULTS.auth_handler_id
        )

        assert res.tag == pending_tag
        final_state = await authorization._load_sign_in_state(context)
        assert final_state is not None
        assert final_state.continuation_activity == original_continuation
        assert final_state.active_handler_id == DEFAULTS.auth_handler_id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, activity_type, activity_name, has_existing_continuation",
        [
            # Teams + invoke + tokenExchange but NO existing continuation_activity → saves
            (
                Channels.ms_teams,
                ActivityTypes.invoke,
                SignInConstants.token_exchange_operation_name,
                False,
            ),
            # Non-Teams channel with all other conditions met → saves
            (
                "directline",
                ActivityTypes.invoke,
                SignInConstants.token_exchange_operation_name,
                True,
            ),
            # Teams channel with non-invoke activity type → saves
            (
                Channels.ms_teams,
                ActivityTypes.message,
                None,
                True,
            ),
            # Teams invoke with a name other than token_exchange → saves
            (
                Channels.ms_teams,
                ActivityTypes.invoke,
                SignInConstants.verify_state_operation_name,
                True,
            ),
        ],
    )
    async def test_saves_state_when_consent_required_condition_not_fully_met(
        self,
        mocker,
        storage,
        authorization,
        pending_tag,
        channel_id,
        activity_type,
        activity_name,
        has_existing_continuation,
    ):
        """When any single condition of the Teams SSO guard is false, the state IS saved."""
        activity_kwargs = dict(
            type=activity_type,
            channel_id=channel_id,
            from_property={"id": DEFAULTS.user_id},
        )
        if activity_name is not None:
            activity_kwargs["name"] = activity_name
        activity = Activity(**activity_kwargs)
        context = create_testing_TurnContext(mocker, activity=activity)

        original_continuation = (
            Activity(type=ActivityTypes.message, text="original")
            if has_existing_continuation
            else None
        )
        initial_state = _SignInState(
            active_handler_id=DEFAULTS.auth_handler_id,
            continuation_activity=original_continuation,
        )
        await authorization._save_sign_in_state(context, initial_state)
        mock_variants(mocker, sign_in_return=_SignInResponse(tag=pending_tag))

        await authorization._start_or_continue_sign_in(
            context, None, DEFAULTS.auth_handler_id
        )

        final_state = await authorization._load_sign_in_state(context)
        assert final_state is not None
        assert final_state.continuation_activity == context.activity
