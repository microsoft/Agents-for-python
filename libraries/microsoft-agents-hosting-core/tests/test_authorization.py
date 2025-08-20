import datetime

import pytest

from microsoft.agents.activity import (
    TokenResponse
)
from microsoft.agents.hosting.core import (
    Authorization,
    MemoryStorage,
    FlowStorageClient,
    FlowState,
    FlowErrorTag,
    FlowStateTag,
    FlowResponse
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
        return context
    
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
    def connection_manager(self):
        pass

    @pytest.fixture
    def auth_handlers(self):
        return {
            "handler": AuthHandler(
                name="handler",
                title="Test Handler",
                text="Text"
                abs_oauth_connection_name="handler",
                obo_connection_name="obo"
            ),
            "connection": AuthHandler(
                name="connection",
                title="Test Handler",
                text="Text"
                abs_oauth_connection_name="connection",
                obo_connection_name="obo"
            )
        }

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

    def test_init(self, mocker):
        pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id", ["", "handler", "missing_handler"])
    async def test_open_flow_value_error(self, auth, context, auth_handler_id):
        with pytest.raises(ValueError):
            async with auth.open_flow(context, auth_handler_id):
                pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ", from_property_id, auth_handler_id",
        [
            ("channel_id", "user_id", "expired"),
            ("teams_id", "Bob", "no_retries"),
            ("channel", "Alice", "begin"),
            ("channel", "Alice", "continue"),
            ("channel", "Alice", "expired_and_retries"),
            ("channel", "Alice", "not_started"),
        ]
    )
    async def test_open_flow_readonly_run(self, mocker, connection_manager, channel_id, from_property_id, auth_handler_id):
        # setup
        storage = MemoryStorage(STORAGE_SAMPLE_DICT)
        baseline = StorageBaseline(STORAGE_SAMPLE_DICT)
        auth = Authorization(
            storage,
            connection_manager,
            auth_handlers
        )
        context = self.build_context(mocker, channel_id, from_property_id)
        storage_client = FlowStorageClient(context, storage)
        key = storage_client.key(auth_handler_id)
        expected_init_flow_state = storage.read(key, FlowState)

        # code
        async with auth.open_flow(context, "handler", readonly=True) as flow:
            actual_init_flow_state = flow.flow_state.copy()
            flow.flow_state.id = "garbage"
            flow.flow_state.tag = FlowStateTag.FAILURE
            flow.flow_state.expires = 0
            flow.flow_state.attempts_remaining = -1
        actual_final_flow_state = await storage.read([key], FlowState)[key]

        # verify
        expected_final_flow_state = baseline.read(key, FlowState)
        assert actual_init_flow_state == expected_init_flow_state
        assert actual_final_flow_state == expected_final_flow_state
        assert await baseline.equals(storage)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, from_property_id, auth_handler_id",
        [
            ("channel_id", "user_id", "expired"),
            ("teams_id", "Bob", "no_retries"),
            ("channel", "Alice", "begin"),
            ("channel", "Alice", "continue"),
            ("channel", "Alice", "expired_and_retries"),
            ("channel", "Alice", "not_started"),
        ]
    )
    async def test_open_flow_storage_run(self, mocker, connection_manager, channel_id, from_property_id, auth_handler_id):
        # setup
        storage = MemoryStorage(STORAGE_SAMPLE_DICT)
        baseline = StorageBaseline(STORAGE_SAMPLE_DICT)
        auth = Authorization(
            storage,
            connection_manager,
            auth_handlers
        )
        context = self.build_context(mocker, channel_id, from_property_id)
        storage_client = FlowStorageClient(context, storage)
        key = storage_client.key(auth_handler_id)
        expected_init_flow_state = storage.read(key, FlowState)

        # code
        async with auth.open_flow(context, "handler") as flow:
            actual_init_flow_state = flow.flow_state.copy()
            flow.flow_state.id = "garbage"
            flow.flow_state.tag = FlowStateTag.FAILURE
            flow.flow_state.expires = 0
            flow.flow_state.attempts_remaining = -1

        # verify
        baseline.write({
            "auth/channel/Alice/continue": flow.flow_state
        })
        expected_final_flow_state = baseline.read(key, FlowState)
        assert await baseline.equals(storage)
        assert actual_init_flow_state == expected_init_flow_state
        assert flow.flow_state == expected_final_flow_state

    @pytest.mark.asyncio
    async def test_get_token(self, mocker, m_storage):
        m_storage.read.return_value = FlowState(
            id="auth_handler",
            tag=FlowStateTag.ACTIVE,
            expires=3600,
            attempts_remaining=3
        )
        expected = TokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=3600
        )
        mock_flow = mocker.AsyncMock()
        mock_flow.get_user_token.return_value = expected
        mocker.patch.object("OAuthFlow", "get_token", return_value=expected)
        mocker.patch.object("OAuthFlow", "__init__", return_value=mock_flow)

        assert await auth.get_token("auth_handler") is expected
        assert mock_flow.get_user_token.called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth, context, auth_handler_id",
        [
            (lazy_fixture("auth"), lazy_fixture("context"), "missing-handler"),
            (lazy_fixture("auth"), lazy_fixture("context"), ""),
            (lazy_fixture("auth"), None, "handler")
        ]
    )
    async def test_get_token_error(self, auth, context, auth_handler_id):
        with pytest.raises(ValueError):
            await auth.get_token(context, auth_handler_id)
    
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