import datetime

import pytest

from microsoft.agents.activity import (
    ActivityTypes,
    TokenResponse
)
from microsoft.agents.hosting.core import (
    Authorization,
    MemoryStorage,
    FlowStorageClient,
    FlowState,
    FlowErrorTag,
    FlowStateTag,
    FlowResponse,
    storage
)
from microsoft.agents.hosting.core.storage.storage_test_utils import StorageBaseline
from microsoft.agents.hosting.core.connector.user_token_base import UserTokenBase
from microsoft.agents.hosting.core.connector.user_token_client_base import UserTokenClientBase

from microsoft.agents.hosting.core.app.oauth.auth_flow import AuthFlow

from tools.oauth_test_utils import (
    TEST_DEFAULTS,
    STORAGE_INIT_DATA
)

from tools.testing_authorization import (
    TestingTokenProvider,
    TestingConnectionManager,
    create_test_auth_handler
)

class TestAuthFlowUtils:

    def create_context(self,
                       mocker,
                       channel_id="__channel_id",
                       user_id="__user_id",
                       abs_oauth_connection_name="graph",
                       user_token_client=None):
        
        if not user_token_client:
            user_token_client = self.create_mock_user_token_client(mocker)

        turn_context = mocker.Mock()
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = user_id
        turn_context.adapter.USER_TOKEN_CLIENT_KEY = "__user_token_client"
        turn_context.turn_state = {
            "__user_token_client": user_token_client
        }
        return turn_context
    
    def create_mock_user_token_client(
        self,
        mocker,
        token=None,
    ):
        mock_user_token_client_class = mocker.Mock(spec=UserTokenClientBase)
        mock_user_token_client_class.user_token = mocker.Mock(spec=UserTokenBase)
        mock_user_token_client_class.user_token.get_token = mocker.AsyncMock(
            return_value=TokenResponse(token=token)
        )
        mock_user_token_client_class.user_token.sign_out = mocker.AsyncMock()
        return mock_user_token_client_class
    
    @pytest.fixture
    def mock_user_token_client_class(self, mocker):
        return self.create_mock_user_token_client_class(mocker)
    
    @pytest.fixture
    def mock_flow_class(self, mocker):
        mock_flow_class = mocker.Mock(spec=AuthFlow)

        mocker.patch.object(AuthFlow, "__init__", return_value=mock_flow_class)
        mock_flow_class.get_user_token = mocker.AsyncMock()
        mock_flow_class.sign_out = mocker.AsyncMock()
        
        return mock_flow_class
    
    @pytest.fixture
    def turn_context(self, mocker):
        return self.create_context(mocker, "__channel_id", "__user_id", "__connection")

    def create_user_token_client(self, mocker, get_token_return=None):

        user_token_client = mocker.Mock(spec=UserTokenClientBase)
        user_token_client.user_token = mocker.Mock(spec=UserTokenBase)
        user_token_client.user_token.get_token = mocker.AsyncMock()
        user_token_client.user_token.sign_out = mocker.AsyncMock()
        
        return_value = TokenResponse()
        if get_token_return:
            return_value = TokenResponse(token=get_token_return)
        user_token_client.user_token.get_token.return_value = return_value

        return user_token_client
    
    @pytest.fixture
    def user_token_client(self, mocker):
        return self.create_user_token_client(mocker, get_token_return=TEST_DEFAULTS.RES_TOKEN)

    def create_activity(self, mocker, activity_type=ActivityTypes.message, name="a", value=None, text="a"):
        # def conv_ref():
        #     return mocker.MagicMock(spec=ConversationReference)
        mock_conversation_ref = mocker.MagicMock(ConversationReference)
        mocker.patch.object(Activity, "get_conversation_reference", return_value=mocker.MagicMock(ConversationReference))
        # mocker.patch.object(ConversationReference, "create", return_value=conv_ref())
        return Activity(
            type=activity_type,
            name=name,
            from_property=ChannelAccount(id=TEST_DEFAULTS.USER_ID),
            channel_id=TEST_DEFAULTS.CHANNEL_ID,
            # get_conversation_reference=mocker.Mock(return_value=conv_ref),
            relates_to=mocker.MagicMock(ConversationReference),
            value=value,
            text=text
        )

    @pytest.fixture(params=TEST_DEFAULTS.ALL())
    def sample_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=TEST_DEFAULTS.FAILED())
    def sample_failed_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=TEST_DEFAULTS.INACTIVE())
    def sample_inactive_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=TEST_DEFAULTS.ACTIVE())
    def sample_active_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture
    def flow(self, sample_flow_state, user_token_client):
        return AuthFlow(sample_flow_state, user_token_client)
    
    @pytest.fixture
    def auth_handlers(self):
        handlers = {}
        for key in STORAGE_INIT_DATA().keys():
            if key.startswith("auth/"):
                auth_handler_name = key[key.rindex("/")+1:]
                handlers[auth_handler_name] = create_test_auth_handler(auth_handler_name, True)
        return handlers
    
    @pytest.fixture
    def connection_manager(self):
        return TestingConnectionManager()

    @pytest.fixture
    def auth(self, connection_manager, storage, auth_handlers):
        return Authorization(connection_manager, storage, auth_handlers)

class TestAuthorizationUtils:

    def create_user_token_client(self, mocker, get_token_return=None):

        user_token_client = mocker.Mock(spec=UserTokenClientBase)
        user_token_client.user_token = mocker.Mock(spec=UserTokenBase)
        user_token_client.user_token.get_token = mocker.AsyncMock()
        user_token_client.user_token.sign_out = mocker.AsyncMock()
        
        return_value = TokenResponse()
        if get_token_return:
            return_value = TokenResponse(token=get_token_return)
        user_token_client.user_token.get_token.return_value = return_value

        return user_token_client

    def create_storage(self):
        return MemoryStorage(STORAGE_INIT_DATA())
    
    @pytest.fixture
    def storage(self):
        return self.create_storage()
    
    @pytest.fixture
    def baseline_storage(self):
        return StorageBaseline(STORAGE_INIT_DATA())
    
    def mock_user_token_provider
    
    def patch_flow(self, mocker, flow_response=None, token=None,):
        mocker.patch.object(AuthFlow, "get_user_token", return_value=TokenResponse(token=token))
        mocker.patch.object(AuthFlow, "sign_out")
        mocker.patch.object(AuthFlow, "begin_or_continue_flow", return_value=flow_response) 

class TestAuthorization(TestAuthorizationUtils):

    def test_init_configuration_variants(self,storage, connection_manager, auth_handlers):
        AGENTAPPLICATION = {
            "USERAUTHORIZATION": {
                "HANDLERS": {
                    handler_name: {
                        "SETTINGS": {
                            "title": handler.title,
                            "text": handler.text,
                            "abs_oauth_connection_name": handler.abs_oauth_connection_name,
                            "obo_connection_name": handler.obo_connection_name
                        }
                    } for handler_name, handler in auth_handlers.items()
                }
            }
        }
        auth_with_config_obj = Authorization(
            storage,
            connection_manager,
            auth_handlers=None,
            AGENTAPPLICATION=AGENTAPPLICATION
        )
        auth_with_handlers_list = Authorization(
            storage,
            connection_manager,
            auth_handlers=auth_handlers
        )
        for auth_handler_name in auth_handlers.keys():
            auth_handler_a = auth_with_config_obj.resolve_handler(auth_handler_name)
            auth_handler_b = auth_with_handlers_list.resolve_handler(auth_handler_name)
            assert auth_handler_a == auth_handler_b

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id, channel_id, user_id",
        [
            ["", "webchat", "Alice"]
            ["handler", "teams", "Bob"]
        ])
    async def test_open_flow_value_error(
        self,
        mocker,
        auth,
        auth_handler_id,
        channel_id,
        user_id
    ):
        context = self.create_context(mocker, channel_id, user_id)
        with pytest.raises(ValueError):
            async with auth.open_flow(context, auth_handler_id):
                pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id, channel_id, user_id",
        [
            ["", "webchat", "Alice"],
            ["handler", "teams", "Bob"]
        ])
    async def test_open_flow_readonly(
        self,
        storage,
        connection_client,
        auth_handlers,
        auth_handler_id,
        channel_id,
        user_id
    ):
        # setup
        context = self.create_context(mocker, channel_id, user_id)
        auth = Authorization(storage, connection_client, auth_handlers)
        flow_storage_client = FlowStorageClient(context, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_open_flow_not_in_storage(
        self,
        mocker,
        storage,
        connection_manager,
        auth_handlers
    ):
        # setup
        context = self.create_context(mocker, "__channel_id", "__user_id")
        auth = Authorization(storage, connection_manager, auth_handlers)
        flow_storage_client = FlowStorageClient(context, storage)
        
        # test
        async with auth.open_flow(context, "__auth_handler_id") as flow:
            assert flow is not None
            assert isinstance(flow, AuthFlow)
        flow_state = await flow_storage_client.read("__auth_handler_id")

        # verify
        assert flow_state.channel_id == "__channel_id"
        assert flow_state.user_id == "__user_id"
        assert flow_state.auth_handler_id == "__auth_handler_id"
        assert flow_state.tag == FlowStateTag.NOT_STARTED

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_complete_flow(
        self,
        mocker,
        storage,
        connection_client, 
        auth_handlers,
        auth_handler_id,
        channel_id,
        user_id
    ):
        # setup
        channel_id = "teams"
        user_id = "Alice"
        auth_handler_id = "graph"

        self.create_user_token_client(
            mocker,
            get_token_return=TokenResponse(token=TEST_DEFAULTS.RES_TOKEN)
        )

        context = self.create_context(mocker, channel_id, user_id)
        context.activity.type = ActivityTypes.message
        context.activity.text = "123456"

        auth = Authorization(storage, connection_client, auth_handlers)
        flow_storage_client = FlowStorageClient(context, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.COMPLETE
            expected_flow_state.user_token = TEST_DEFAULTS.RES_TOKEN

            flow_response = await flow.begin_or_continue_flow(context.activity)
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expires_at = actual_flow_state.expires_at # we won't check this for now

        assert res_flow_state == expected_flow_state
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_failure(
        self,
        mocker,
        baseline_storage,
        storage,
        connection_client,
        auth_handlers,
        auth_handler_id,
        channel_id,
        user_id
    ):
        # setup
        channel_id = "webchat"
        user_id = "Bob"
        auth_handler_id = "graph"

        context = self.create_context(mocker, channel_id, user_id)

        auth = Authorization(storage, connection_client, auth_handlers)
        flow_storage_client = FlowStorageClient(context, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.FAILURE
            expected_flow_state.attempts_remaining = 0

            flow_response = await flow.begin_or_continue_flow(context.activity)
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expires_at = actual_flow_state.expires_at # we won't check this for now

        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_FORMAT
        assert res_flow_state == expected_flow_state
        assert actual_flow_state == expected_flow_state

        baseline_storage.write(res_flow_state.model_copy())
        assert await baseline_storage.equals(storage)

    @pytest.mark.asyncio
    async def test_open_flow_success_modified_signout(
        self,
        mocker,
        storage,
        connection_client,
        auth_handlers,
        auth_handler_id,
        channel_id,
        user_id
    ):
        # setup
        channel_id = "webchat"
        user_id = "Alice"
        auth_handler_id = "graph"

        context = self.create_context(mocker, channel_id, user_id)

        auth = Authorization(storage, connection_client, auth_handlers)
        flow_storage_client = FlowStorageClient(context, storage)

        # test
        async with auth.open_flow(context, auth_handler_id) as flow:
            expected_flow_state = flow.flow_state
            expected_flow_state.tag = FlowStateTag.FAILURE
            expected_flow_state.user_token = ""

            flow_response = await flow.sign_out()
            res_flow_state = flow_response.flow_state

        # verify
        actual_flow_state = await flow_storage_client.read(auth_handler_id)
        expected_flow_state.expires_at = actual_flow_state.expires_at # we won't check this for now

        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_FORMAT
        assert res_flow_state == expected_flow_state
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_get_token_success(
        self,
        mocker,
        auth
    ):
        mock_user_token_client_class = self.create_user_token_client(
            mocker,
            get_token_return=TokenResponse(token="token")
        )
        context = self.create_context(mocker, "__channel_id", "__user_id")
        assert await auth.get_token(context, "auth_handler") == TokenResponse(token="token")
        mock_user_token_client_class.get_user_token.called_once()

    @pytest.mark.asyncio
    async def test_get_token_empty_response(
        self,
        mocker,
        auth
    ):
        mock_user_token_client_class = self.create_user_token_client(
            mocker,
            get_token_return=TokenResponse()
        )
        context = self.create_context(mocker, "__channel_id", "__user_id")
        assert await auth.get_token(context, "auth_handler") == TokenResponse()
        mock_user_token_client_class.get_user_token.called_once()

    @pytest.mark.asyncio
    async def test_get_token_error(
        self,
        turn_context,
        storage,
        connection_manager,
        auth_handlers
    ):
        auth = Authorization(storage, connection_manager, auth_handlers)
        with pytest.raises(ValueError):
            await auth.get_token(turn_context, "missing-handler")

    @pytest.mark.asyncio
    async def test_exchange_token_no_token(
        self,
        turn_context,
        mock_auth_flow_class,
        mocker,
        auth
    ):
        mock_auth_flow_class.get_user_token = mocker.AsyncMock(
            return_value=TokenResponse()
        )
        res = await auth.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "token",
        [
            "token",
            ""
        ] # robrandao: TODOTODO
    )
    async def test_exchange_token_not_exchangeable(
        self,
        mock_auth_flow_class,
        turn_context,
        mocker,
        auth,
        token
    ):
        mock_auth_flow_class.get_user_token = mocker.AsyncMock(
            return_value=TokenResponse(token=token)
        )
        res = await auth.exchange_token(turn_context, ["scope"], "github")
        assert res == TokenResponse()
    
    @pytest.fixture
    def valid_token_response(self):
        return TokenResponse(
            connection_name="connection",
            token="token"
        )
    
    @pytest.fixture
    def invalid_exchange_token(self):
        token = jwt.encode({"aud": "invalid://botframework.test.api"}, "")
        return TokenResponse(
            connection_name="connection"
            token=token
        )

    @pytest.mark.asyncio
    async def test_exchange_token(
        self,
        mock_user_token_client_class,
    ):
        
        mocker.patch.object("OAuthFlow",
            get_user_token=mocker.AsyncMock(return_value=TokenResponse(
                access_token="access_token",
                refresh_token="refresh_token",
                expires_in=3600
            ))
        )
        mock_user_token_client_class

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, user_id, expected_flow_state",
        [
            []
        ]
    )
    async def test_get_active_flow_state(self, mocker, auth, channel_id, user_id, expected_flow_state):
        context = self.create_context(mocker, channel_id, user_id)
        actual_flow_state = await auth.get_active_flow_state(context)
        assert actual_flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_get_active_flow_state_missing(self, mocker, auth):
        context = self.create_context(mocker, "__channel_id", "__user_id")
        res = await auth.get_active_flow_state(context)
        assert res is None

    @pytest.mark.asyncio
    async def begin_or_continue_flow(
        self,
        mocker,
        turn_context,
        storage,
        baseline_storage,
        connection_manager,
        auth_handlers
    ):
        pass

    @pytest.mark.parametrize("auth_handler_id", ["handler", "connection"])
    def test_resolve_handler_specified(self, auth, auth_handlers, auth_handler_id):
        assert auth.resolve_handler(auth_handler_id) == auth_handlers[auth_handler_id]

    def test_resolve_handler_error(self, auth):
        with pytest.raises(ValueError):
            auth.resolve_handler("missing-handler")

    def test_resolve_handler_first(self, auth, auth_handlers_list):
        assert auth.resolve_handler() == auth_handlers_list[0]

    @pytest.mark.asyncio
    async def test_sign_out_individual(
        self,
        mock_user_token_client_class,
        mock_flow_class,
        turn_context,
        storage,
        baseline_storage,
        connection_manager,
        auth_handlers
    ):
        # setup
        storage_client = FlowStorageClient(turn_context, storage)

        auth = Authorization(storage, connection_manager, auth_handlers)
        await auth.sign_out("handler")

        await baseline_storage.delete([storage_client.key("handler")])

        # verify storage
        assert await baseline_storage.equals(storage)

        # verify flow
        mock_flow_class.sign_out.assert_called_once_with("handler")
        mock_user_token_client_class.user_token.sign_out.assert_called_once()

    @pytest.mark.asyncio
    async def test_sign_out_all(
        self,
        mock_user_token_client_class,
        mock_flow_class,
        turn_context,
        storage,
        baseline_storage,
        connection_manager,
        auth_handlers
    ):
        # setup
        storage_client = FlowStorageClient(turn_context, storage)

        auth = Authorization(storage, connection_manager, auth_handlers)
        await auth.sign_out("handler")

        await baseline_storage.delete([storage_client.key("handler"), storage_client.key("connection")])

        # verify storage
        assert await baseline_storage.equals(storage)

        # verify flow
        mock_flow_class.sign_out.assert_called_once_with("handler")
        mock_flow_class.sign_out.assert_called_once_with("connection")


    # robrandao: TODO -> handlers