import pytest
from datetime import datetime
import jwt

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    TokenResponse
)

from microsoft_agents.hosting.core import (
    FlowStorageClient,
    FlowErrorTag,
    FlowStateTag,
    FlowState,
    FlowResponse,
    OAuthFlow,
    Authorization,
    UserAuthorization,
    MemoryStorage,
    AuthHandler,
    FlowStateTag,
)
from microsoft_agents.hosting.core.app.auth import SignInState

from tests._common.storage.utils import StorageBaseline

# test constants
from tests._common.data import (
    TEST_FLOW_DATA,
    TEST_AUTH_DATA,
    TEST_STORAGE_DATA,
    TEST_DEFAULTS,
    TEST_ENV_DICT,
    TEST_AGENTIC_ENV_DICT,
    create_test_auth_handler,
)
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import (
    TestingConnectionManager as MockConnectionManager,
    mock_class_OAuthFlow,
    mock_UserTokenClient,
    mock_class_UserAuthorization,
    mock_class_AgenticAuthorization,
    mock_class_Authorization
)
from tests.hosting_core._common import flow_state_eq

from ._common import testing_TurnContext, testing_Activity

DEFAULTS = TEST_DEFAULTS()
FLOW_DATA = TEST_FLOW_DATA()
STORAGE_DATA = TEST_STORAGE_DATA()
ENV_DICT = TEST_ENV_DICT()
AGENTIC_ENV_DICT = TEST_AGENTIC_ENV_DICT()

def get_sign_in_state(auth: Authorization, storage: Storage, context: TurnContext) -> Optional[SignInState]:
    key = auth.get_sign_in_state_key(context)
    return storage.read([key], target_cls=SignInState).get(key)

def set_sign_in_state(auth: Authorization, storage: Storage, context: TurnContext, state: SignInState):
    key = auth.get_sign_in_state_key(context)
    storage.write({key: state})


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

class TestAuthorizationSetup(TestEnv):

    def test_init_user_auth(self, connection_manager, storage, env_dict):
        auth = Authorization(storage, connection_manager, **env_dict)
        assert auth.user_auth is not None

    def test_init_agentic_auth_not_configured(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        with pytest.raises(ValueError):
            agentic_auth = auth.agentic_auth

    def test_init_agentic_auth(self, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)
        assert auth.agentic_auth is not None

    @pytest.mark.parametrize("auth_handler_id", [DEFAULTS.auth_handler_id, DEFAULTS.agentic_auth_handler_id])
    def test_resolve_handler(self, connection_manager, storage, auth_handler_id):
        auth = Authorization(storage, connection_manager, **AGENTIC_ENV_DICT)
        handler_config = AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][auth_handler_id]
        auth.resolve_handler(auth_handler_id) == AuthHandler(auth_handler_id, **handler_config)

    def test_sign_in_state_key(self, mocker, connection_manager, storage):
        auth = Authorization(storage, connection_manager, **ENV_DICT)
        context = self.TurnContext(mocker)
        key = auth.sign_in_state_key(context)
        assert key == f"auth:SignInState:{DEFAULTS.channel_id}:{DEFAULTS.user_id}"
    
class TestAuthorizationUsage(TestEnv):

    @pytest.mark.asyncio
    async def test_get_token(self, mocker, storage, authorization):
        context = self.TurnContext(mocker)
        token_response = await authorization.get_token(context, DEFAULTS.auth_handler_id)
        assert not token_response


    @pytest.mark.asyncio
    async def test_get_token_with_sign_in_state_empty(self, mocker, storage, authorization, context):
        # setup
        key = authorization.get_sign_in_state_key(context)
        storage.write({key: SignInState(
            tokens={DEFAULTS.auth_handler_id: "", DEFAULTS.agentic_auth_handler_id: ""}
        )})

        # test
        token_response = await authorization.get_token(context, DEFAULTS.auth_handler_id)
        assert not token_response

    @pytest.mark.asyncio
    async def test_get_token_with_sign_in_state_empty_alt(self, mocker, storage, authorization, context):
        # setup
        key = authorization.get_sign_in_state_key(context)
        storage.write({key: SignInState(
            tokens={DEFAULTS.auth_handler_id: "token", DEFAULTS.agentic_auth_handler_id: ""}
        )})

        # test
        token_response = await authorization.get_token(context, DEFAULTS.agentic_auth_handler_id)
        assert not token_response

    @pytest.mark.asyncio
    async def test_get_token_with_sign_in_state_valid(self, mocker, storage, authorization):
        # setup
        context = self.TurnContext(mocker)
        key = authorization.get_sign_in_state_key(context)
        storage.write({key: SignInState(
            tokens={DEFAULTS.auth_handler_id: "valid_token"}
        )})

        # test
        token_response = await authorization.get_token(context, DEFAULTS.auth_handler_id)
        assert token_response.token == "valid_token"

    def test_start_or_continue_sign_in_cached(self, storage, authorization, context, activity):
        # setup
        initial_state = SignInState(
            tokens={DEFAULTS.auth_handler_id: "valid_token"}, continuation_activity=activity
        )
        set_sign_in_state(authorization, storage, context, initial_state)
        assert await authorization.start_or_continue_sign_in(context, None, DEFAULTS.auth_handler_id)
        assert get_sign_in_state(authorization, storage, context) == initial_state

    def test_start_or_continue_sign_in_no_state_to_complete(self, mocker, storage, authorization, context):
        mock_class_UserAuthorization(mocker, sign_in_return=SignInResponse(
            token_response=TokenResponse(token=DEFAULTS.token),
            tag=FlowStateTag.COMPLETE
        ))
        await authorization.start_or_continue_sign_in(context, None, DEFAULTS.auth_handler_id)


        assert not await authorization.start_or_continue_sign_in(context, None, DEFAULTS.auth_handler_id)
        assert get_sign_in_state(authorization, storage, context) is None