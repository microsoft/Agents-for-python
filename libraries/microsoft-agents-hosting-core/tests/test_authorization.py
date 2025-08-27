import pytest

import jwt

from microsoft_agents.activity import ActivityTypes, TokenResponse
from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.storage.storage_test_utils import StorageBaseline
from microsoft_agents.hosting.core.connector.user_token_base import UserTokenBase
from microsoft_agents.hosting.core.connector.user_token_client_base import (
    UserTokenClientBase,
)

from microsoft_agents.hosting.core.app.oauth import Authorization
from microsoft_agents.hosting.core.oauth import (
    FlowStorageClient,
    FlowErrorTag,
    FlowStateTag,
    FlowResponse,
    OAuthFlow,
)

# test constants
from .tools.testing_oauth import *
from .tools.testing_authorization import (
    TestingConnectionManager as MockConnectionManager,
    create_test_auth_handler,
)


class TestUtils:

    def create_context(
        self,
        mocker,
        channel_id="__channel_id",
        user_id="__user_id",
        user_token_client=None,
    ):

        if not user_token_client:
            user_token_client = self.create_mock_user_token_client(mocker)

        turn_context = mocker.Mock()
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = user_id
        turn_context.activity.type = ActivityTypes.message
        turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
        turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
        agent_identity = mocker.Mock()
        agent_identity.claims = {"aud": MS_APP_ID}
        turn_context.turn_state = {
            "__user_token_client": user_token_client,
            "__agent_identity_key": agent_identity,
        }
        return turn_context

    def create_mock_user_token_client(
        self,
        mocker,
        token=RES_TOKEN,
    ):
        mock_user_token_client_class = mocker.Mock(spec=UserTokenClientBase)
        mock_user_token_client_class.user_token = mocker.Mock(spec=UserTokenBase)
        mock_user_token_client_class.user_token.get_token = mocker.AsyncMock(
            return_value=TokenResponse() if not token else TokenResponse(token=token)
        )
        mock_user_token_client_class.user_token.sign_out = mocker.AsyncMock()
        return mock_user_token_client_class

    @pytest.fixture
    def mock_user_token_client_class(self, mocker):
        return self.create_mock_user_token_client(mocker)

    def create_mock_oauth_flow_class(self, mocker, token_response):
        mock_oauth_flow_class = mocker.Mock(spec=OAuthFlow)
        # mock_oauth_flow_class.get_user_token = mocker.AsyncMock(return_value=token_response)
        # mock_oauth_flow_class.sign_out = mocker.AsyncMock()
        mocker.patch.object(OAuthFlow, "get_user_token", return_value=token_response)
        mocker.patch.object(OAuthFlow, "sign_out")
        return mock_oauth_flow_class

    @pytest.fixture
    def mock_oauth_flow_class(self, mocker):
        return self.create_mock_oauth_flow_class(mocker, TokenResponse(token=RES_TOKEN))
        # mock_flow_class = mocker.Mock(spec=OAuthFlow)

        # # mocker.patch.object(OAuthFlow, "__init__", return_value=mock_flow_class)
        # mock_flow_class.get_user_token = mocker.AsyncMock(return_value=TokenResponse(token=RES_TOKEN))
        # mock_flow_class.sign_out = mocker.AsyncMock()
        # mocker.patch.object(OAuthFlow, "get_user_token")

        # return mock_flow_class

    @pytest.fixture
    def turn_context(self, mocker):
        return self.create_context(mocker, "__channel_id", "__user_id", "__connection")

    def create_user_token_client(self, mocker, get_token_return=""):

        user_token_client = mocker.Mock(spec=UserTokenClientBase)
        user_token_client.user_token = mocker.Mock(spec=UserTokenBase)
        user_token_client.user_token.get_token = mocker.AsyncMock()
        user_token_client.user_token.sign_out = mocker.AsyncMock()

        return_value = TokenResponse()
        if isinstance(get_token_return, TokenResponse):
            return_value = get_token_return
        elif get_token_return:
            return_value = TokenResponse(token=get_token_return)
        user_token_client.user_token.get_token.return_value = return_value

        return user_token_client

    @pytest.fixture
    def user_token_client(self, mocker):
        return self.create_user_token_client(mocker, get_token_return=RES_TOKEN)

    @pytest.fixture
    def auth_handlers(self):
        handlers = {}
        for key in STORAGE_INIT_DATA().keys():
            if key.startswith("auth/"):
                auth_handler_name = key[key.rindex("/") + 1 :]
                handlers[auth_handler_name] = create_test_auth_handler(
                    auth_handler_name, True
                )
        return handlers

    @pytest.fixture
    def connection_manager(self):
        return MockConnectionManager()

    @pytest.fixture
    def auth(self, connection_manager, storage, auth_handlers):
        return Authorization(storage, connection_manager, auth_handlers)


class TestAuthorizationUtils(TestUtils):

    def create_storage(self):
        return MemoryStorage(STORAGE_INIT_DATA())

    @pytest.fixture
    def storage(self):
        return self.create_storage()

    @pytest.fixture
    def baseline_storage(self):
        return StorageBaseline(STORAGE_INIT_DATA())

    def patch_flow(
        self,
        mocker,
        flow_response=None,
        token=None,
    ):
        mocker.patch.object(
            OAuthFlow, "get_user_token", return_value=TokenResponse(token=token)
        )
        mocker.patch.object(OAuthFlow, "sign_out")
        mocker.patch.object(
            OAuthFlow, "begin_or_continue_flow", return_value=flow_response
        )


class TestAuthorization(TestAuthorizationUtils):

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
        auth_with_config_obj = Authorization(
            storage,
            connection_manager,
            auth_handlers=None,
            AGENTAPPLICATION=AGENTAPPLICATION,
        )
        auth_with_handlers_list = Authorization(
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
        self, mocker, auth, auth_handler_id, channel_id, user_id
    ):
        """Test opening a flow with a missing auth handler."""
        context = self.create_context(mocker, channel_id, user_id)
        with pytest.raises(ValueError):
            async with auth.open_flow(context, auth_handler_id):
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
        context = self.create_context(mocker, channel_id, user_id)
        auth = Authorization(storage, connection_manager, auth_handlers)
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
        mock_user_token_client_class,
        auth_handlers,
    ):
        # setup
        channel_id = "teams"
        user_id = "Alice"
        auth_handler_id = "graph"

        self.create_user_token_client(mocker, get_token_return=RES_TOKEN)

        context = self.create_context(mocker, channel_id, user_id)
        context.activity.type = ActivityTypes.message
        context.activity.text = "123456"

        auth = Authorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.COMPLETE
            expected_flow_state.user_token = RES_TOKEN

            flow_response = await flow.begin_or_continue_flow(context.activity)
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expiration = (
            res_flow_state.expiration
        )  # we won't check this for now

        assert res_flow_state == expected_flow_state
        assert actual_flow_state == expected_flow_state

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

        context = self.create_context(mocker, channel_id, user_id)
        context.activity.text = "invalid_magic_code"

        auth = Authorization(storage, connection_manager, auth_handlers)
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
        expected_flow_state.expiration = (
            actual_flow_state.expiration
        )  # we won't check this for now

        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_FORMAT
        assert res_flow_state == expected_flow_state
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_signout(
        self, mocker, storage, connection_manager, auth_handlers
    ):
        # setup
        channel_id = "webchat"
        user_id = "Alice"
        auth_handler_id = "graph"

        context = self.create_context(mocker, channel_id, user_id)

        auth = Authorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(channel_id, user_id, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.NOT_STARTED
            expected_flow_state.user_token = ""

            await flow.sign_out()

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expiration = (
            actual_flow_state.expiration
        )  # we won't check this for now
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_get_token_success(self, mocker, auth):
        mock_user_token_client_class = self.create_user_token_client(
            mocker, get_token_return=TokenResponse(token="token")
        )
        context = self.create_context(
            mocker,
            "__channel_id",
            "__user_id",
            user_token_client=mock_user_token_client_class,
        )
        assert await auth.get_token(context, "slack") == TokenResponse(token="token")
        mock_user_token_client_class.user_token.get_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_token_empty_response(self, mocker, auth):
        mock_user_token_client_class = self.create_user_token_client(
            mocker, get_token_return=TokenResponse()
        )
        context = self.create_context(
            mocker,
            "__channel_id",
            "__user_id",
            user_token_client=mock_user_token_client_class,
        )
        assert await auth.get_token(context, "graph") == TokenResponse()
        mock_user_token_client_class.user_token.get_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_token_error(
        self, turn_context, storage, connection_manager, auth_handlers
    ):
        auth = Authorization(storage, connection_manager, auth_handlers)
        with pytest.raises(ValueError):
            await auth.get_token(turn_context, "missing-handler")

    @pytest.mark.asyncio
    async def test_exchange_token_no_token(self, mocker, turn_context, auth):
        self.create_mock_oauth_flow_class(mocker, TokenResponse())
        res = await auth.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()

    @pytest.mark.asyncio
    async def test_exchange_token_not_exchangeable(self, mocker, turn_context, auth):
        token = jwt.encode({"aud": "invalid://botframework.test.api"}, "")
        self.create_mock_oauth_flow_class(
            mocker, TokenResponse(connection_name="github", token=token)
        )
        res = await auth.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()

    @pytest.mark.asyncio
    async def test_exchange_token_valid_exchangeable(self, turn_context, mocker, auth):
        token = jwt.encode({"aud": "api://botframework.test.api"}, "")
        self.create_mock_oauth_flow_class(
            mocker, TokenResponse(connection_name="github", token=token)
        )
        mock_user_token_client_class = self.create_mock_user_token_client(
            mocker, token=token
        )
        mock_user_token_client_class.user_token.exchange_token = mocker.AsyncMock(
            return_value=TokenResponse(
                scopes=["scope"], token=token, connection_name="github"
            )
        )
        res = await auth.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse(token="github-obo-connection-obo-token")

    @pytest.mark.asyncio
    async def test_get_active_flow_state(self, mocker, auth):
        context = self.create_context(mocker, "webchat", "Alice")
        actual_flow_state = await auth.get_active_flow_state(context)
        assert (
            actual_flow_state
            == STORAGE_SAMPLE_DICT[flow_key("webchat", "Alice", "github")]
        )

    @pytest.mark.asyncio
    async def test_get_active_flow_state_missing(self, mocker, auth):
        context = self.create_context(mocker, "__channel_id", "__user_id")
        res = await auth.get_active_flow_state(context)
        assert res is None

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_success(self, mocker, auth):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        mocker.patch.object(
            OAuthFlow,
            "begin_or_continue_flow",
            return_value=FlowResponse(
                token_response=TokenResponse(token="token"),
                flow_state=FlowState(
                    tag=FlowStateTag.COMPLETE, auth_handler_id="github"
                ),
            ),
        )
        context = self.create_context(mocker, "webchat", "Alice")

        context.dummy_val = None

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        auth.on_sign_in_success(on_sign_in_success)
        auth.on_sign_in_failure(on_sign_in_failure)
        flow_response = await auth.begin_or_continue_flow(context, None, "github")
        assert context.dummy_val == "github"
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_already_completed(self, mocker, auth):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        context = self.create_context(mocker, "webchat", "Alice")

        context.dummy_val = None

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        auth.on_sign_in_success(on_sign_in_success)
        auth.on_sign_in_failure(on_sign_in_failure)
        flow_response = await auth.begin_or_continue_flow(context, None, "graph")
        assert context.dummy_val == None
        assert flow_response.token_response == TokenResponse(token="test_token")
        assert flow_response.continuation_activity is None

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_failure(
        self, mocker, mock_oauth_flow_class, auth
    ):
        # robrandao: TODO -> lower priority -> more testing here
        # setup
        mocker.patch.object(
            OAuthFlow,
            "begin_or_continue_flow",
            return_value=FlowResponse(
                token_response=TokenResponse(token="token"),
                flow_state=FlowState(
                    tag=FlowStateTag.FAILURE, auth_handler_id="github"
                ),
                flow_state_error=FlowErrorTag.MAGIC_FORMAT,
            ),
        )
        context = self.create_context(mocker, "webchat", "Alice")

        context.dummy_val = None

        def on_sign_in_success(context, turn_state, auth_handler_id):
            context.dummy_val = auth_handler_id

        def on_sign_in_failure(context, turn_state, auth_handler_id, err):
            context.dummy_val = str(err)

        # test
        auth.on_sign_in_success(on_sign_in_success)
        auth.on_sign_in_failure(on_sign_in_failure)
        flow_response = await auth.begin_or_continue_flow(context, None, "github")
        assert context.dummy_val == "FlowErrorTag.NONE"
        assert flow_response.token_response == TokenResponse(token="token")

    @pytest.mark.parametrize("auth_handler_id", ["graph", "github"])
    def test_resolve_handler_specified(self, auth, auth_handlers, auth_handler_id):
        assert auth.resolve_handler(auth_handler_id) == auth_handlers[auth_handler_id]

    def test_resolve_handler_error(self, auth):
        with pytest.raises(ValueError):
            auth.resolve_handler("missing-handler")

    def test_resolve_handler_first(self, auth, auth_handlers):
        assert auth.resolve_handler() == next(iter(auth_handlers.values()))

    @pytest.mark.asyncio
    async def test_sign_out_individual(
        self,
        mocker,
        mock_user_token_client_class,
        mock_oauth_flow_class,
        storage,
        baseline_storage,
        connection_manager,
        auth_handlers,
    ):
        # setup
        storage_client = FlowStorageClient("teams", "Alice", storage)
        context = self.create_context(mocker, "teams", "Alice")
        auth = Authorization(storage, connection_manager, auth_handlers)

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
        mock_user_token_client_class,
        mock_oauth_flow_class,
        turn_context,
        storage,
        baseline_storage,
        connection_manager,
        auth_handlers,
    ):
        # setup
        storage_client = FlowStorageClient("webchat", "Alice", storage)

        auth = Authorization(storage, connection_manager, auth_handlers)
        context = self.create_context(mocker, "webchat", "Alice")
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
