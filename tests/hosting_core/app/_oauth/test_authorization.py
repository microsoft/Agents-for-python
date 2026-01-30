import pytest
import jwt

from typing import Optional

from microsoft_agents.activity import Activity, ActivityTypes, TokenResponse

from microsoft_agents.hosting.core.app.oauth import (
    _SignInResponse,
    _SignInState,
    _UserAuthorization,
    Authorization,
    AgenticUserAuthorization,
)

from microsoft_agents.hosting.core._oauth import _FlowStateTag

from microsoft_agents.hosting.core import (
    AuthHandler,
    Storage,
    MemoryStorage,
    TurnContext,
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
    mock_UserTokenClient,
    mock_class_UserAuthorization,
    mock_class_AgenticUserAuthorization,
    mock_class_Authorization,
)

from ._common import create_testing_TurnContext, create_testing_Activity

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
        self.UserTokenClient = mock_UserTokenClient
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
                _SignInState(active_handler_id="some_value_bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJV0E="),
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
                _SignInState(active_handler_id="some_value_bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJV0E="),
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
        "initial_cache, final_cache, auth_handler_id, expected_auth_handler_id, initial_sign_in_state, final_sign_in_state, sign_in_response",
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
    async def test_on_turn_auth_intercept_no_intercept(
        self, storage, authorization, context
    ):
        await authorization._delete_sign_in_state(context)

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, None
        )

        assert not continuation_activity
        assert not intercepts

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

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, auth_handler_id
        )

        assert not continuation_activity
        assert intercepts

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

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, auth_handler_id
        )

        assert continuation_activity == old_activity
        assert intercepts

        final_state = await authorization._load_sign_in_state(context)
        assert sign_in_state_eq(final_state, initial_state)
        assert context.turn_state == expected_cache
