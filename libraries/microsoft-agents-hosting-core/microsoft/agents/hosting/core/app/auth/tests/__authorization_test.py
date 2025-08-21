import datetime

import pytest
from pytest_lazyfixture import lazy_fixture

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
from microsoft.agents.hosting.core.app.oauth.auth_flow import (
    AuthFlow
)
from microsoft.agents.hosting.core.storage.storage_test_utils import StorageBaseline

def mock_flow(mocker, flow_states: list[FlowState]):
    flow = mocker.Mock(spec=AuthFlow)
    flow.begin_or_continue_flow = mocker.AsyncMock(
        side_effect=flow_states
    )
    return flow

STORAGE_SAMPLE_DICT = {
    "user_id": "123",
    "session_id": "abc",
    "auth/channel_id/user_id/expired": FlowState(
        id="expired",
        expires=expired_time,
        attempts_remaining=1,
        tag=FlowStateTag.CONTINUE
    ),
    "auth/teams_id/Bob/no_retries": FlowState(
        id="no_retries",
        expires=valid_time,
        attempts_remaining=0,
        tag=FlowStateTag.FAILURE
    ),
    "auth/channel/Alice/begin": FlowState(
        id="begin",
        expired=valid_time,
        attempts_remaining=3,
        tag=FlowStateTag.BEGIN
    ),
    "auth/channel/Alice/continue": FlowState(
        id="continue",
        expires=valid_time,
        attempts_remaining=2
        tag=FlowStateTag.CONTINUE
    ),
    "auth/channel/Alice/expired_and_retries": FlowState(
        id="expired_and_retries"
        expires=expired_time,
        attempts_remaining=0
        tag=FlowStateTag.FAILURE
    ),
    "auth/channel/Alice/not_started": FlowState(
        id="not_started",
        tag=FlowStateTag.NOT_STARTED
    )
}

class TestAuthorization:

    def build_context(self, mocker, channel_id, from_property_id):
        turn_context = mocker.Mock()
        turn_context.activity.channel_id = channel_id
        turn_context.activity.from_property.id = from_property_id
        return turn_context
    
    @pytest.fixture

    @pytest.fixture
    def context(self, mocker):
        return self.build_context(mocker, "__channel_id", "__user_id")
    
    @pytest.fixture
    def valid_time(self):
        return datetime.datetime.now() + 10000

    @pytest.fixture
    def expired_time(self):
        return datetime.datetime.now()
    
    @pytest.fixture
    def m_storage(self, mocker):
        return mocker.Mock(spec=MemoryStorage)
    
    @pytest.fixture
    def m_connection_manager(self, mocker):
        return mocker.Mock(spec=ConnectionManager)
    
    @pytest.fixture
    def auth_handler_ids(self):
        return ["expired", "no_retries", "begin", "continue", "expired_and_retries", "not_started"]

    @pytest.fixture
    def auth_handlers(self, mocker, auth_handler_ids):
        return {
            auth_handler_id: create_test_auth_handler(f"test-{auth_handler_id}") for auth_handler_id in auth_handler_ids
        }
    
    @pytest.fixture
    def storage(self, valid_time, expired_time):
        return MemoryStorage(STORAGE_SAMPLE_DICT)

    @pytest.fixture
    def connection_manager(self):
        pass

    @pytest.fixture
    def auth_handlers(self):
        pass

    @pytest.fixture
    def auth(self, storage, connection_manager, auth_handlers):
        return Authorization(
            storage,
            connection_manager,
            auth_handlers,
            auto_signin=True
        )
    
    @pytest.fixture
    def storage(self, mocker):
        return MemoryStorage({
           
        })
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth, context, auth_handler_id",
        [
            ("auth", lazy_fixture("context"), ""),
            ("auth", None, "handler"),
            ("auth", None, "")
            ("auth", lazy_fixture("context", "missing_handler"))
        ],
        indirect=["auth"]
    )
    async def test_open_flow_value_error(self, auth, context, auth_handler_id):
        with pytest.raises(ValueError):
            async with auth.open_flow(context, auth_handler_id):
                pass

    # async def test_open_flow_storage_readonly_storage_access(self, mocker, context, m_storage, m_connection_manager, m_auth_handlers):
    #     # setup
    #     m_storage.read.return_value = FlowState()
    #     auth = Authorization(
    #         m_storage,
    #         m_connection_manager,
    #         m_auth_handlers
    #     )

    #     # code
    #     async with auth.open_flow(context, "handler", readonly=True) as flow:
    #         actual_init_flow_state = flow.flow_state
        
    #     # verify
    #     assert actual_init_flow_state is m_storage.read.return_value
    #     assert not m_storage.write.called
    #     assert not m_storage.delete.called

    # async def test_open_flow_storage_unchanged_not_readonly_storage_access(self, context, m_storage, m_connection_manager, m_auth_handlers):
    #     # setup
    #     m_storage.read.return_value = FlowState()
    #     auth = Authorization(
    #         m_storage,
    #         m_connection_manager,
    #         m_auth_handlers
    #     )

    #     # code
    #     async with auth.open_flow(context, "handler", readonly=False) as flow:
    #         # if no change is made to the flow state, then storage should not be updated
    #         actual_init_flow_state = flow.flow_state
        
    #     # verify
    #     assert actual_init_flow_state is m_storage.read.return_value
    #     assert not m_storage.write.called
    #     assert not m_storage.delete.called

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, connection_manager, channel_id, from_property_id, auth_handler_id",
        [
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel_id", "user_id", "expired"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "teams_id", "Bob", "no_retries"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "begin"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "continue"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "expired_and_retries"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "not_started"),
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
        "mocker, connection_manager, channel_id, from_property_id, auth_handler_id",
        [
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel_id", "user_id", "expired"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "teams_id", "Bob", "no_retries"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "begin"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "continue"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "expired_and_retries"),
            (lazy_fixture("mocker"), lazy_fixture("connection_manager"), "channel", "Alice", "not_started"),
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
    @pytest.mark.parametrize
    async def test_exchange_token(self, mocker, auth):
        
        mocker.patch.object("OAuthFlow",
            get_user_token=mocker.AsyncMock(return_value=TokenResponse(
                access_token="access_token",
                refresh_token="refresh_token",
                expires_in=3600
            ))
        )



        

    @pytest.mark.asyncio
    async def test_exchange_token(self):
        pass