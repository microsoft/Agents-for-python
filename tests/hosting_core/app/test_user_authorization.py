import pytest
from datetime import datetime
import jwt

from microsoft_agents.activity import ActivityTypes, TokenResponse

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
STORAGE_DATA = TEST_STORAGE_DATA()


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
        return UserAuthorization(storage, connection_manager, auth_handlers)


class TestAuthorization(TestEnv):
    def test_init_configuration_variants(
        self, storage, connection_manager, auth_handlers
    ):
        """Test initialization of authorization with different configuration variants."""
        AGENTAPPLICATION = {
            "USERAUTHORIZATION": {
                "HANDLERS": {
                    handler_name: {
                        "SETTINGS": {
                            "title": handler.title,
                            "text": handler.text,
                            "abs_oauth_connection_name": handler.abs_oauth_connection_name,
                            "obo_connection_name": handler.obo_connection_name,
                        }
                    }
                    for handler_name, handler in auth_handlers.items()
                }
            }
        }
        auth_with_config_obj = UserAuthorization(
            storage,
            connection_manager,
            auth_handlers=None,
            AGENTAPPLICATION=AGENTAPPLICATION,
        )
        auth_with_handlers_list = UserAuthorization(
            storage, connection_manager, auth_handlers=auth_handlers
        )
        for auth_handler_name in auth_handlers.keys():
            auth_handler_a = auth_with_config_obj.resolve_handler(auth_handler_name)
            auth_handler_b = auth_with_handlers_list.resolve_handler(auth_handler_name)

            assert auth_handler_a.name == auth_handler_b.name
            assert auth_handler_a.title == auth_handler_b.title
            assert auth_handler_a.text == auth_handler_b.text
            assert (
                auth_handler_a.abs_oauth_connection_name
                == auth_handler_b.abs_oauth_connection_name
            )
            assert (
                auth_handler_a.obo_connection_name == auth_handler_b.obo_connection_name
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id, channel_id, user_id",
        [["missing", "webchat", "Alice"], ["handler", "teams", "Bob"]],
    )
    async def test_open_flow_value_error(
        self, mocker, user_authorization, auth_handler_id, channel_id, user_id
    ):
        """Test opening a flow with a missing auth handler."""
        context = self.TurnContext(mocker, channel_id=channel_id, user_id=user_id)
        with pytest.raises(ValueError):
            async with user_authorization.open_flow(context, auth_handler_id):
                pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id, channel_id, user_id",
        [
            ["", "webchat", "Alice"],
            ["graph", "teams", "Bob"],
            ["slack", "webchat", "Chuck"],
        ],
    )
    async def test_open_flow_readonly(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers,
        auth_handler_id,
        channel_id,
        user_id,
    ):
        """Test opening a flow and not modifying it."""
        # setup
        context = self.TurnContext(mocker, channel_id=channel_id, user_id=user_id)
        auth = UserAuthorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(
            auth.resolve_handler(auth_handler_id).name
        )
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_complete_flow(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers,
    ):
        # mock
        channel_id = "teams"
        user_id = "Alice"
        auth_handler_id = "graph"

        user_token_client = self.UserTokenClient(
            mocker, get_token_return=DEFAULTS.token
        )
        context = self.TurnContext(
            mocker,
            channel_id=channel_id,
            user_id=user_id,
            user_token_client=user_token_client,
        )

        # setup
        context.activity.type = ActivityTypes.message
        context.activity.text = "123456"

        auth = UserAuthorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.COMPLETE
            expected_flow_state.user_token = DEFAULTS.token

            flow_response = await flow.begin_or_continue_flow(context.activity)
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expiration = actual_flow_state.expiration
        assert flow_state_eq(actual_flow_state, expected_flow_state)
        assert flow_state_eq(res_flow_state, expected_flow_state)

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_failure(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers,
    ):
        # setup
        channel_id = "teams"
        user_id = "Bob"
        auth_handler_id = "slack"

        context = self.TurnContext(mocker, channel_id=channel_id, user_id=user_id)
        context.activity.text = "invalid_magic_code"

        auth = UserAuthorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.FAILURE
            expected_flow_state.attempts_remaining = 0

            flow_response = await flow.begin_or_continue_flow(context.activity)
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)

        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_FORMAT
        assert flow_state_eq(res_flow_state, expected_flow_state)
        assert flow_state_eq(actual_flow_state, expected_flow_state)

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_signout(
        self, mocker, storage, connection_manager, auth_handlers
    ):
        # setup
        channel_id = "webchat"
        user_id = "Alice"
        auth_handler_id = "graph"

        context = self.TurnContext(mocker, channel_id=channel_id, user_id=user_id)

        auth = UserAuthorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.NOT_STARTED
            expected_flow_state.user_token = ""

            await flow.sign_out()

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        assert flow_state_eq(actual_flow_state, expected_flow_state)

    @pytest.mark.asyncio
    async def test_get_token_success(self, mocker, user_authorization):
        user_token_client = self.UserTokenClient(mocker, get_token_return="token")
        context = self.TurnContext(
            mocker,
            channel_id="__channel_id",
            user_id="__user_id",
            user_token_client=user_token_client,
        )
        assert await user_authorization.get_token(context, "slack") == TokenResponse(
            token="token"
        )
        user_token_client.user_token.get_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_token_empty_response(self, mocker, user_authorization):
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse()
        )
        context = self.TurnContext(
            mocker,
            channel_id="__channel_id",
            user_id="__user_id",
            user_token_client=user_token_client,
        )
        assert await user_authorization.get_token(context, "graph") == TokenResponse()
        user_token_client.user_token.get_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_token_error(
        self, turn_context, storage, connection_manager, auth_handlers
    ):
        auth = UserAuthorization(storage, connection_manager, auth_handlers)
        with pytest.raises(ValueError):
            await auth.get_token(
                turn_context, DEFAULTS.missing_abs_oauth_connection_name
            )

    @pytest.mark.asyncio
    async def test_exchange_token_no_token(self, mocker, turn_context, user_authorization):
        mock_class_OAuthFlow(mocker, get_user_token_return=TokenResponse())
        res = await user_authorization.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()

    @pytest.mark.asyncio
    async def test_exchange_token_not_exchangeable(
        self, mocker, turn_context, user_authorization
    ):
        token = jwt.encode({"aud": "invalid://botframework.test.api"}, "")
        mock_class_OAuthFlow(
            mocker,
            get_user_token_return=TokenResponse(connection_name="github", token=token),
        )
        res = await user_authorization.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()

    @pytest.mark.asyncio
    async def test_exchange_token_valid_exchangeable(self, mocker, user_authorization):
        # setup
        token = jwt.encode({"aud": "api://botframework.test.api"}, "")
        mock_class_OAuthFlow(
            mocker,
            get_user_token_return=TokenResponse(connection_name="github", token=token),
        )
        user_token_client = self.UserTokenClient(
            mocker, get_token_return="github-obo-connection-obo-token"
        )
        turn_context = self.TurnContext(mocker, user_token_client=user_token_client)
        # test
        res = await user_authorization.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse(token="github-obo-connection-obo-token")

    @pytest.mark.asyncio
    async def test_get_active_flow_state(self, mocker, user_authorization):
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")
        actual_flow_state = await user_authorization.get_active_flow_state(context)
        assert actual_flow_state == STORAGE_DATA.dict["auth/webchat/Alice/github"]

    @pytest.mark.asyncio
    async def test_get_active_flow_state_missing(self, mocker, user_authorization):
        context = self.TurnContext(
            mocker, channel_id="__channel_id", user_id="__user_id"
        )
        res = await user_authorization.get_active_flow_state(context)
        assert res is None

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

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        user_authorization.on_sign_in_success(on_sign_in_success)
        user_authorization.on_sign_in_failure(on_sign_in_failure)
        flow_response = await user_authorization.begin_or_continue_flow(
            context, None, "github"
        )
        assert context.dummy_val == "github"
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_already_completed(
        self, mocker, user_authorization
    ):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        context = self.TurnContext(mocker, channel_id="webchat", user_id="Alice")

        context.dummy_val = None

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        user_authorization.on_sign_in_success(on_sign_in_success)
        user_authorization.on_sign_in_failure(on_sign_in_failure)
        flow_response = await user_authorization.begin_or_continue_flow(
            context, None, "graph"
        )
        assert context.dummy_val == None
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
        context.dummy_val = None

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        user_authorization.on_sign_in_success(on_sign_in_success)
        user_authorization.on_sign_in_failure(on_sign_in_failure)
        flow_response = await user_authorization.begin_or_continue_flow(
            context, None, "github"
        )
        assert context.dummy_val == "FlowErrorTag.MAGIC_FORMAT"
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.parametrize("auth_handler_id", ["graph", "github"])
    def test_resolve_handler_specified(
        self, user_authorization, auth_handlers, auth_handler_id
    ):
        assert (
            user_authorization.resolve_handler(auth_handler_id)
            == auth_handlers[auth_handler_id]
        )

    def test_resolve_handler_error(self, user_authorization):
        with pytest.raises(ValueError):
            user_authorization.resolve_handler("missing-handler")

    def test_resolve_handler_first(self, user_authorization, auth_handlers):
        assert user_authorization.resolve_handler() == next(iter(auth_handlers.values()))

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
