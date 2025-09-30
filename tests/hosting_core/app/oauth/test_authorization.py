import pytest
import jwt

from typing import Optional

from microsoft_agents.activity import Activity, ActivityTypes, TokenResponse

from microsoft_agents.hosting.core.app.oauth import (
    _SignInResponse,
    _SignInState,
    _UserAuthorization,
    Authorization,
    AgenticUserAuthorization
)

from microsoft_agents.hosting.core._oauth import _FlowStateTag

from microsoft_agents.hosting.core import (
    AuthHandler,
    Storage,
    MemoryStorage,
    TurnContext
)


from tests._common.storage.utils import StorageBaseline

# test constants
from tests._common.data import (
    TEST_FLOW_DATA,
    TEST_AUTH_DATA,
    TEST_STORAGE_DATA,
    TEST_DEFAULTS,
    TEST_ENV_DICT,
    TEST_AGENTIC_ENV_DICT,
)
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import (
    TestingConnectionManager as MockConnectionManager,
    mock_UserTokenClient,
    mock_class_UserAuthorization,
    mock_class_AgenticUserAuthorization,
    mock_class_Authorization,
)

from ._common import testing_TurnContext, testing_Activity

DEFAULTS = TEST_DEFAULTS()
FLOW_DATA = TEST_FLOW_DATA()
STORAGE_DATA = TEST_STORAGE_DATA()
ENV_DICT = TEST_ENV_DICT()
AGENTIC_ENV_DICT = TEST_AGENTIC_ENV_DICT()

def make_jwt(token: str = DEFAULTS.token, aud="api://default"):
    if aud:
        return jwt.encode({"aud": aud}, token, algorithm="HS256")
    else:
        return jwt.encode({}, token, algorithm="HS256")

async def get_sign_in_state(
    auth: Authorization, storage: Storage, context: TurnContext
) -> Optional[_SignInState]:
    key = auth._sign_in_state_key(context)
    return (await storage.read([key], target_cls=_SignInState)).get(key)


async def set_sign_in_state(
    auth: Authorization, storage: Storage, context: TurnContext, state: _SignInState
):
    key = auth._sign_in_state_key(context)
    await storage.write({key: state})


def mock_variants(mocker, sign_in_return=None, get_refreshed_token_return=None):
    mock_class_UserAuthorization(mocker, sign_in_return=sign_in_return, get_refreshed_token_return=get_refreshed_token_return)
    mock_class_AgenticUserAuthorization(mocker, sign_in_return=sign_in_return, get_refreshed_token_return=get_refreshed_token_return)

def sign_in_state_eq(a: Optional[_SignInState], b: Optional[_SignInState]) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a.tokens == b.tokens and a.continuation_activity == b.continuation_activity


def copy_sign_in_state(state: _SignInState) -> _SignInState:
    return _SignInState(
        tokens=state.tokens.copy(),
        continuation_activity=(
            state.continuation_activity.model_copy()
            if state.continuation_activity
            else None
        ),
    )


class TestEnv(FlowStateFixtures):
    def setup_method(self):
        self.TurnContext = testing_TurnContext
        self.UserTokenClient = mock_UserTokenClient
        self.ConnectionManager = lambda mocker: MockConnectionManager()

    @pytest.fixture
    def context(self, mocker):
        return self.TurnContext(mocker)

    @pytest.fixture
    def activity(self):
        return testing_Activity()

    @pytest.fixture
    def baseline_storage(self):
        return StorageBaseline(TEST_STORAGE_DATA().dict)

    @pytest.fixture
    def storage(self):
        return MemoryStorage(STORAGE_DATA.get_init_data())

    @pytest.fixture
    def connection_manager(self, mocker):
        return self.ConnectionManager(mocker)

    @pytest.fixture
    def auth_handlers(self):
        return TEST_AUTH_DATA().auth_handlers

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
        assert isinstance(auth._resolve_handler(DEFAULTS.auth_handler_id), _UserAuthorization)

    def test_init_agentic_auth_not_configured(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        with pytest.raises(ValueError):
            auth._resolve_handler(DEFAULTS.agentic_auth_handler_id)

    def test_init_agentic_auth(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)
        assert auth._resolve_handler(DEFAULTS.agentic_auth_handler_id) is not None
        assert isinstance(auth._resolve_handler(DEFAULTS.agentic_auth_handler_id), AgenticUserAuthorization)

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
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    async def test_sign_out_not_signed_in(
        self, mocker, storage, authorization, context, activity, auth_handler_id
    ):
        mock_variants(mocker)
        initial_state = _SignInState(
            tokens={DEFAULTS.auth_handler_id: "", "my_handler": "old_token"},
            continuation_activity=activity,
        )
        await set_sign_in_state(
            authorization, storage, context, copy_sign_in_state(initial_state)
        )
        await authorization.sign_out(context, None, auth_handler_id)
        final_state = await get_sign_in_state(authorization, storage, context)
        if auth_handler_id in initial_state.tokens:
            del initial_state.tokens[auth_handler_id]
        assert sign_in_state_eq(final_state, initial_state)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    async def test_sign_out_signed_in(
        self, mocker, storage, authorization, context, activity, auth_handler_id
    ):
        mock_variants(mocker)
        initial_state = _SignInState(
            tokens={
                DEFAULTS.auth_handler_id: "token",
                DEFAULTS.agentic_auth_handler_id: "another_token",
                "my_handler": "old_token",
            },
            continuation_activity=activity,
        )
        await set_sign_in_state(
            authorization, storage, context, copy_sign_in_state(initial_state)
        )
        await authorization.sign_out(context, None, auth_handler_id)
        final_state = await get_sign_in_state(authorization, storage, context)
        del initial_state.tokens[auth_handler_id]
        assert sign_in_state_eq(final_state, initial_state)

    @pytest.mark.asyncio
    async def test_start_or_continue_sign_in_cached(
        self, storage, authorization, context, activity
    ):
        # setup
        initial_state = _SignInState(
            tokens={DEFAULTS.auth_handler_id: "valid_token"},
            continuation_activity=activity,
        )
        await set_sign_in_state(authorization, storage, context, initial_state)
        sign_in_response = await authorization._start_or_continue_sign_in(
            context, None, DEFAULTS.auth_handler_id
        )
        assert sign_in_response.tag == _FlowStateTag.COMPLETE
        assert sign_in_response.token_response.token == "valid_token"

        assert sign_in_state_eq(
            await get_sign_in_state(authorization, storage, context), initial_state
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    async def test_start_or_continue_sign_in_no_initial_state_to_complete(
        self, mocker, storage, authorization, context, auth_handler_id
    ):
        mock_variants(
            mocker,
            sign_in_return=_SignInResponse(
                token_response=TokenResponse(token=DEFAULTS.token),
                tag=_FlowStateTag.COMPLETE,
            ),
        )
        sign_in_response = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )
        assert sign_in_response.tag == _FlowStateTag.COMPLETE
        assert sign_in_response.token_response.token == DEFAULTS.token

        final_state = await get_sign_in_state(authorization, storage, context)
        assert final_state.tokens[auth_handler_id] == DEFAULTS.token
        assert final_state.continuation_activity is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    async def test_start_or_continue_sign_in_to_complete_with_prev_state(
        self, mocker, storage, authorization, context, auth_handler_id
    ):
        # setup
        initial_state = _SignInState(
            tokens={"my_handler": "old_token"},
            continuation_activity=Activity(
                type=ActivityTypes.message, text="old activity"
            ),
        )
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(
            mocker,
            sign_in_return=_SignInResponse(
                token_response=TokenResponse(token=DEFAULTS.token),
                tag=_FlowStateTag.COMPLETE,
            ),
        )

        # test
        sign_in_response = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )
        assert sign_in_response.tag == _FlowStateTag.COMPLETE
        assert sign_in_response.token_response.token == DEFAULTS.token

        # verify
        final_state = await get_sign_in_state(authorization, storage, context)
        assert final_state.tokens[auth_handler_id] == DEFAULTS.token
        assert final_state.tokens["my_handler"] == "old_token"
        assert final_state.continuation_activity == initial_state.continuation_activity

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id]
    )
    async def test_start_or_continue_sign_in_to_failure_with_prev_state(
        self, mocker, storage, authorization, context, auth_handler_id
    ):
        # setup
        initial_state = _SignInState(
            tokens={"my_handler": "old_token"},
            continuation_activity=Activity(
                type=ActivityTypes.message, text="old activity"
            ),
        )
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(
            mocker,
            sign_in_return=_SignInResponse(
                token_response=TokenResponse(), tag=_FlowStateTag.FAILURE
            ),
        )

        # test
        sign_in_response = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )
        assert sign_in_response.tag == _FlowStateTag.FAILURE
        assert not sign_in_response.token_response

        # verify
        final_state = await get_sign_in_state(authorization, storage, context)
        assert not final_state.tokens.get(auth_handler_id)
        assert final_state.tokens["my_handler"] == "old_token"
        assert final_state.continuation_activity == initial_state.continuation_activity

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id, tag",
        [
            (DEFAULTS.auth_handler_id, _FlowStateTag.BEGIN),
            (DEFAULTS.agentic_auth_handler_id, _FlowStateTag.BEGIN),
            (DEFAULTS.auth_handler_id, _FlowStateTag.CONTINUE),
            (DEFAULTS.agentic_auth_handler_id, _FlowStateTag.CONTINUE),
        ],
    )
    async def test_start_or_continue_sign_in_to_pending_with_prev_state(
        self, mocker, storage, authorization, context, auth_handler_id, tag
    ):
        # setup
        initial_state = _SignInState(
            tokens={"my_handler": "old_token"},
            continuation_activity=Activity(
                type=ActivityTypes.message, text="old activity"
            ),
        )
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(
            mocker,
            sign_in_return=_SignInResponse(token_response=TokenResponse(), tag=tag),
        )

        # test
        sign_in_response = await authorization._start_or_continue_sign_in(
            context, None, auth_handler_id
        )
        assert sign_in_response.tag == tag
        assert not sign_in_response.token_response

        # verify
        final_state = await get_sign_in_state(authorization, storage, context)
        assert not final_state.tokens.get(auth_handler_id)
        assert final_state.tokens["my_handler"] == "old_token"
        assert final_state.continuation_activity == context.activity

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_state, final_state, handler_id, refresh_token, expected",
        [
            [ # no cached token
                _SignInState(
                    tokens={DEFAULTS.auth_handler_id: "token"},
                ),
                _SignInState(
                    tokens={DEFAULTS.auth_handler_id: "token"},
                ),
                DEFAULTS.agentic_auth_handler_id,
                TokenResponse(),
                TokenResponse()
            ],
            [ # no cached token and default handler id resolution
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token"},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token"},
                ),
                "",
                TokenResponse(),
                TokenResponse()
            ],
            [ # no cached token pt.2
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token", DEFAULTS.auth_handler_id: ""},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token", DEFAULTS.auth_handler_id: ""},
                ),
                DEFAULTS.auth_handler_id,
                TokenResponse(),
                TokenResponse()
            ],
            [ # refreshed, new token
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: make_jwt(), DEFAULTS.auth_handler_id: ""},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: DEFAULTS.token, DEFAULTS.auth_handler_id: ""},
                ),
                DEFAULTS.agentic_auth_handler_id,
                TokenResponse(token=DEFAULTS.token),
                TokenResponse(token=DEFAULTS.token)
            ],
        ]
    )
    async def test_get_token(self, mocker, authorization, context, storage, initial_state, final_state, handler_id, refresh_token, expected):
        # setup
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(mocker, get_refreshed_token_return=refresh_token)

        # test
        token = await authorization.get_token(context, handler_id)
        assert token == expected

        final_state = await get_sign_in_state(authorization, storage, context)
        assert sign_in_state_eq(initial_state, final_state)

    @pytest.mark.asyncio
    async def test_get_token_error(self, mocker, authorization, context, storage):
        initial_state = _SignInState(
            tokens={DEFAULTS.auth_handler_id: "old_token"},
        )
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(mocker, get_refreshed_token_return=TokenResponse())
        with pytest.raises(Exception):
            await authorization.get_token(context, DEFAULTS.auth_handler_id)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_state, final_state, handler_id, refreshed, refresh_token, expected",
        [
            [ # no cached token
                _SignInState(
                    tokens={DEFAULTS.auth_handler_id: "token"},
                ),
                _SignInState(
                    tokens={DEFAULTS.auth_handler_id: "token"},
                ),
                DEFAULTS.agentic_auth_handler_id,
                False,
                TokenResponse(),
                TokenResponse()
            ],
            [ # no cached token and default handler id resolution
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token"},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token"},
                ),
                "",
                False,
                TokenResponse(),
                TokenResponse()
            ],
            [ # no cached token pt.2
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token", DEFAULTS.auth_handler_id: ""},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: "token", DEFAULTS.auth_handler_id: ""},
                ),
                DEFAULTS.auth_handler_id,
                False,
                TokenResponse(),
                TokenResponse()
            ],
            [ # refreshed, new token
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: make_jwt(), DEFAULTS.auth_handler_id: ""},
                ),
                _SignInState(
                    tokens={DEFAULTS.agentic_auth_handler_id: DEFAULTS.token, DEFAULTS.auth_handler_id: ""},
                ),
                DEFAULTS.agentic_auth_handler_id,
                True,
                TokenResponse(token=DEFAULTS.token),
                TokenResponse(token=DEFAULTS.token)
            ],
        ]
    )
    async def test_exchange_token(self, mocker, authorization, context, storage, initial_state, final_state, handler_id, refreshed, refresh_token, expected):
        # setup
        await set_sign_in_state(authorization, storage, context, initial_state)
        mock_variants(mocker, get_refreshed_token_return=refresh_token)

        # test
        token_res = await authorization.exchange_token(context, auth_handler_id=handler_id, exchange_connection="some_connection", scopes=["scope1", "scope2"])
        assert token_res == expected

        final_state = await get_sign_in_state(authorization, storage, context)
        assert sign_in_state_eq(initial_state, final_state)
        if refreshed:
            authorization._resolve_handler(handler_id).get_refreshed_token.assert_called_once_with(
                context,
                "some_connection",
                ["scope1", "scope2"],
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "sign_in_state",
        [
            _SignInState(),
            _SignInState(
                tokens={DEFAULTS.auth_handler_id: "token"},
                continuation_activity=Activity(
                    type=ActivityTypes.message, text="activity"
                ),
            ),
            _SignInState(
                tokens={
                    DEFAULTS.auth_handler_id: "token",
                    DEFAULTS.agentic_auth_handler_id: "another_token",
                },
                continuation_activity=Activity(
                    type=ActivityTypes.message, text="activity"
                ),
            ),
            _SignInState(
                tokens={DEFAULTS.auth_handler_id: "token", "my_handler": "old_token"},
                continuation_activity=Activity(
                    type=ActivityTypes.message, text="activity"
                ),
            ),
        ],
    )
    async def test_on_turn_auth_intercept_no_intercept(
        self, storage, authorization, context, sign_in_state
    ):
        await set_sign_in_state(
            authorization, storage, context, copy_sign_in_state(sign_in_state)
        )

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, None
        )

        assert not continuation_activity
        assert not intercepts

        final_state = await get_sign_in_state(authorization, storage, context)

        assert sign_in_state_eq(final_state, sign_in_state)

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

        initial_state = _SignInState(
            tokens={"some_handler": "old_token", auth_handler_id: ""},
            continuation_activity=Activity(
                type=ActivityTypes.message, text="old activity"
            ),
        )
        await set_sign_in_state(
            authorization, storage, context, copy_sign_in_state(initial_state)
        )

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, auth_handler_id
        )

        assert not continuation_activity
        assert intercepts

        final_state = await get_sign_in_state(authorization, storage, context)
        assert sign_in_state_eq(final_state, initial_state)

    @pytest.mark.asyncio
    async def test_on_turn_auth_intercept_with_intercept_complete(
        self, mocker, storage, authorization, context, auth_handler_id
    ):
        mock_class_Authorization(
            mocker,
            start_or_continue_sign_in_return=_SignInResponse(tag=_FlowStateTag.COMPLETE),
        )

        old_activity = Activity(type=ActivityTypes.message, text="old activity")
        initial_state = _SignInState(
            tokens={"some_handler": "old_token", auth_handler_id: ""},
            continuation_activity=old_activity,
        )
        await set_sign_in_state(
            authorization, storage, context, copy_sign_in_state(initial_state)
        )

        intercepts, continuation_activity = await authorization._on_turn_auth_intercept(
            context, auth_handler_id
        )

        assert continuation_activity == old_activity
        assert intercepts

        # start_or_continue_sign_in is the only method that modifies the state,
        # so since it is mocked, the state should not be changed
        final_state = await get_sign_in_state(authorization, storage, context)
        assert sign_in_state_eq(final_state, initial_state)
