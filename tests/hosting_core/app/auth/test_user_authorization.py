import pytest
from datetime import datetime
import jwt

from microsoft_agents.activity import Activity, ActivityTypes, TokenResponse

from microsoft_agents.hosting.core import (
    FlowStorageClient,
    FlowErrorTag,
    FlowStateTag,
    FlowState,
    FlowResponse,
    OAuthFlow,
    UserAuthorization,
    MemoryStorage,
)

from tests._common.storage.utils import StorageBaseline

# test constants
from tests._common.data import (
    TEST_FLOW_DATA,
    TEST_AUTH_DATA,
    TEST_STORAGE_DATA,
    TEST_DEFAULTS,
    TEST_ENV_DICT,
    create_test_auth_handler,
)
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import (
    TestingConnectionManager as MockConnectionManager,
    mock_class_OAuthFlow,
    mock_UserTokenClient,
)
from tests.hosting_core._common import flow_state_eq

DEFAULTS = TEST_DEFAULTS()
FLOW_DATA = TEST_FLOW_DATA()
ENV_DICT = TEST_ENV_DICT()
STORAGE_DATA = TEST_STORAGE_DATA()


class MyUserAuthorization(UserAuthorization):
    def _handle_flow_response(self, *args, **kwargs):
        pass


def testing_TurnContext(
    mocker,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    user_token_client=None,
):
    if not user_token_client:
        user_token_client = mock_UserTokenClient(mocker)

    turn_context = mocker.Mock()
    turn_context.activity.channel_id = channel_id
    turn_context.activity.from_property.id = user_id
    turn_context.activity.type = ActivityTypes.message
    turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
    turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.turn_state = {
        "__user_token_client": user_token_client,
        "__agent_identity_key": agent_identity,
    }
    return turn_context


class TestEnv(FlowStateFixtures):
    def setup_method(self):
        self.TurnContext = testing_TurnContext
        self.UserTokenClient = mock_UserTokenClient
        self.ConnectionManager = lambda mocker: MockConnectionManager()

    @pytest.fixture
    def turn_context(self, mocker):
        return self.TurnContext(mocker)

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
    def user_authorization(self, connection_manager, storage, auth_handlers):
        return UserAuthorization(
            storage, connection_manager, auth_handlers=auth_handlers
        )


class TestUserAuthorization(TestEnv):

    # TODO -> test init

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_success(self, mocker, user_authorization):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        mock_class_OAuthFlow(
            mocker,
            begin_or_continue_flow_return=FlowResponse(
                token_response=TokenResponse(token="token"),
                flow_state=FlowState(
                    tag=FlowStateTag.COMPLETE, auth_handler_id="github"
                ),
            ),
        )
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")
        context.dummy_val = None

        flow_response = await user_authorization.begin_or_continue_flow(
            context, "github"
        )
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_already_completed(
        self, mocker, user_authorization
    ):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")
        # test
        flow_response = await user_authorization.begin_or_continue_flow(
            context, "graph"
        )
        assert flow_response.token_response == TokenResponse(token="test_token")
        assert flow_response.continuation_activity is None

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_failure(self, mocker, user_authorization):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        mock_class_OAuthFlow(
            mocker,
            begin_or_continue_flow_return=FlowResponse(
                token_response=TokenResponse(token="token"),
                flow_state=FlowState(
                    tag=FlowStateTag.FAILURE, auth_handler_id="github"
                ),
                flow_error_tag=FlowErrorTag.MAGIC_FORMAT,
            ),
        )
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")
        # test
        flow_response = await user_authorization.begin_or_continue_flow(
            context, "github"
        )
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.asyncio
    async def test_sign_out_individual(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers,
    ):
        # setup
        mock_class_OAuthFlow(mocker)
        storage_client = FlowStorageClient("teams", "Alice", storage)
        context = self.TurnContext(mocker, channel_id="teams", user_id="Alice")
        auth = UserAuthorization(storage, connection_manager, auth_handlers)

        # test
        await auth.sign_out(context, "graph")

        # verify
        assert (
            await storage.read([storage_client.key("graph")], target_cls=FlowState)
            == {}
        )
        OAuthFlow.sign_out.assert_called_once()

    @pytest.mark.asyncio
    async def test_sign_out_all(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers,
    ):
        # setup
        mock_class_OAuthFlow(mocker)
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")
        storage_client = FlowStorageClient("webchat", "Alice", storage)
        auth = UserAuthorization(storage, connection_manager, auth_handlers)

        # test
        await auth.sign_out(context)

        # verify
        assert (
            await storage.read([storage_client.key("graph")], target_cls=FlowState)
            == {}
        )
        assert (
            await storage.read([storage_client.key("github")], target_cls=FlowState)
            == {}
        )
        assert (
            await storage.read([storage_client.key("slack")], target_cls=FlowState)
            == {}
        )
        OAuthFlow.sign_out.assert_called()  # ignore red squiggly -> mocked

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "flow_response",
        [
            FlowResponse(
                token_response=TokenResponse(token="token"),
                flow_state=FlowState(
                    tag=FlowStateTag.COMPLETE, auth_handler_id="github"
                ),
            ),
            FlowResponse(
                token_response=TokenResponse(),
                flow_state=FlowState(
                    tag=FlowStateTag.CONTINUE, auth_handler_id="github"
                ),
                continuation_activity=Activity(
                    type=ActivityTypes.message, text="Please sign in"
                ),
            ),
            FlowResponse(
                token_response=TokenResponse(token="wow"),
                flow_state=FlowState(
                    tag=FlowStateTag.FAILURE, auth_handler_id="github"
                ),
                flow_error_tag=FlowErrorTag.MAGIC_FORMAT,
                continuation_activity=Activity(
                    type=ActivityTypes.message, text="There was an error"
                ),
            ),
        ],
    )
    async def test_sign_in_success(
        self, mocker, user_authorization, turn_context, flow_response
    ):
        mocker.patch.object(
            user_authorization, "_handle_flow_response", return_value=None
        )
        user_authorization.begin_or_continue_flow = mocker.AsyncMock(
            return_value=flow_response
        )
        res = await user_authorization.sign_in(turn_context, "github")
        assert res.token_response == flow_response.token_response
        assert res.tag == flow_response.flow_state.tag
