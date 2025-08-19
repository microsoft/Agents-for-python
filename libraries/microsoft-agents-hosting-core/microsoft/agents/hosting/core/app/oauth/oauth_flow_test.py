import pytest

from microsoft.agents.activity import (
    ActivityTypes,
    TokenResponse
)
from microsoft.agents.hosting.core import AuthFlow

from microsoft.agents.hosting.core.app.oauth.models import (
    FlowErrorTag,
    FlowState,
    FlowStateTag,
    FlowResponse
)

class TestAuthFlow:

    @pytest.fixture
    def turn_context(self, mocker):
        context = mocker.Mock()
        context.activity.channel_id = "__channel_id"
        context.activity.from_property.id = "__user_id"
        return context

    def test_init_no_state(self):
        flow = AuthFlow()
        assert flow.flow_state == FlowState()

    def test_init_with_state(self):
        flow_state = FlowState(
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=1,
            expires_at=datetime.now().timestamp() + 10000
        )
        flow = AuthFlow(flow_state=flow_state)
        assert flow.flow_state == flow_state

    @pytest.mark.asyncio
    async def test_get_user_token(self, turn_context):
        # mock
        user_token_client = pytest.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value="test_token")

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
        )
        token = await flow.get_user_token(turn_context)
        
        # verify
        assert token == "test_token"
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            magic_code=None
        )

    @pytest.mark.asyncio
    async def test_sign_out(self, turn_context):
        # mock
        user_token_client = pytest.Mock()
        user_token_client.user_token.sign_out = pytest.AsyncMock()

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="connection",
            user_token_client=user_token_client,
        )
        await flow.sign_out(turn_context)

        # verify
        assert user_token_client.user_token.sign_out.called_once_with(
            user_id="__user_id",
            connection_name="connection",
            channel_id="__channel_id",
            magic_code=None
        )

    @pytest.mark.asyncio
    async def test_begin_flow_easy_case(self):
        # mock
        user_token_client = pytest.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse(token="test_token"))

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
        )
        response = await flow.begin_flow(turn_context)

        # verify flow_state
        flow_state = flow.flow_state
        assert flow_state.tag == FlowStateTag.COMPLETE
        assert flow_state.token == "test_token"
        assert flow_state.flow_started is False # robrandao: TODO?

        # verify FlowResponse
        assert response.flow_state == flow_state
        assert response.sign_in_resource is None  # No sign-in resource in this case
        assert response.flow_error_tag == FlowErrorTag.NONE
        assert response.token_response == "test_token"
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            # magic_code=None is an implementation detail, and ideally
            # shouldn't be part of the test
            magic_code=None
        )

    @pytest.mark.asyncio
    async def test_begin_flow_long_case(self, mocker, turn_context):
        # mock
        dummy_sign_in_resource = SignInResource(
            sign_in_link="https://example.com/signin",
            token_exchange_state=TokenExchangeState(connection_name="test_connection")
        )
        user_token_client = mocker.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse())
        user_token_client.agent_sign_in.get_sign_in_resource = pytest.AsyncMock(return_value=dummy_sign_in_resource)

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
        )
        response = await flow.begin_flow(turn_context)

        # verify flow_state
        flow_state = flow.flow_state
        assert flow_state.tag == FlowStateTag.BEGIN
        assert flow_state.token == ""
        assert flow_state.flow_started is True

        # verify FlowResponse
        assert response.flow_state == flow_state
        assert response.sign_in_resource == dummy_sign_in_resource
        assert response.flow_error_tag == FlowErrorTag.NONE
        assert not response.token_response
        # robrandao: TODO more assertions on sign_in_resource

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker", "turn_context, flow_state",
        [
            ("mocker", "turn_context", FlowState(
                tag=FlowStateTag.BEGIN,
                token="",
                expires=datetime.now().timestamp() - 1,
                attempts_remaining=3
            )),
            ("mocker", "turn_context", FlowState(
                tag=FlowStateTag.CONTINUE,
                token="",
                expires=datetime.now().timestamp() + 1000,
                attempts_remaining=0
            )),
            ("mocker", "turn_context", FlowState(
                tag=FlowStateTag.FAILED,
                token="",
                expires=datetime.now().timestamp() + 1000,
                attempts_remaining=3
            )),
            ("mocker", "turn_context", FlowState(
                tag=FlowStateTag.COMPLETED,
                token="",
                expires=datetime.now().timestamp() + 1000,
                attempts_remaining=2
            )),
        ],
        indirect=["mocker", "turn_context"]
    )
    async def test_continue_flow_not_active(self, mocker, turn_context, flow_state):
        user_token_client = mocker.Mock()
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=flow_state
        )
        flow_response = await flow.continue_flow(turn_context)
        assert flow_response.flow_state == flow_state
        assert not flow_response.token_response

    @pytest.fixture(params=[
        (FlowStateTag.ACTIVE, "test_token", 2),
        (FlowStateTag.BEGIN, "", 1),
    ])
    def active_flow_state(self, request):
        tag, token, attempts_remaining = request.param
        return FlowState(
            tag=tag,
            token=token,
            expires=datetime.now().timestamp() + 1000,
            attempts_remaining=attempts_remaining
        )

    async def test_continue_flow_message(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.text = "magic-message"
        user_token_client = mocker.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse())
        user_token_client.agent_sign_in.get_sign_in_resource = pytest.AsyncMock(return_value=dummy_sign_in_resource)

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=mocker.Mock(),
            flow_state=active_flow_state
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, turn_context, active_flow_state, magic_code",
        [
            ("mocker", "turn_context", "active_flow_state", "magic-message"),
            ("mocker", "turn_context", "active_flow_state", ""),
            ("mocker", "turn_context", "active_flow_state", "abcdef"),
            ("mocker", "turn_context", "active_flow_state", "@#0324"),
            ("mocker", "turn_context", "active_flow_state", "231"),
            ("mocker", "turn_context", "active_flow_state", None),
        ],
        indirect=["mocker", "turn_context", "active_flow_state"]
    )
    async def test_continue_flow_message_format_error(self, mocker, turn_context, active_flow_state, magic_code):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.text = magic_code

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=mocker.Mock(),
            flow_state=active_flow_state
        )
        flow_response = flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining - 1 == flow_response.flow_state.attempts_remaining
        assert not flow_response.token_response
        assert flow_response.tag == FlowStateTag.FAILURE
        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_FORMAT

    @pytest.mark.asyncio
    async def test_continue_flow_message_magic_code_error(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.text = "123456"
        user_token_client = mocker.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse())

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=active_flow_state
        )
        flow_response = await flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining - 1 == flow_response.flow_state.attempts_remaining
        assert not flow_response.token_response
        assert flow_response.flow_error_tag == FlowErrorTag.MAGIC_CODE
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            magic_code="123456"
        )

    @pytest.mark.asyncio
    async def test_continue_flow_invoke_verify_state(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.name = "signin/verifyState"
        turn_context.activity.value = {"state": "987654"}
        user_token_client = mocker.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse(token="some-token"))

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=active_flow_state
        )
        flow_response = await flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining == flow_response.flow_state.attempts_remaining
        assert flow_response.token_response.token == "some-token"
        assert flow_response.flow_state.tag == FlowStateTag.COMPLETE
        assert flow_response.flow_error_tag == FlowErrorTag.NONE
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            magic_code="987654"
        )

    async def test_continue_flow_invoke_verify_state_no_token(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.name = "signin/verifyState"
        turn_context.activity.value = {"state": "987654"}
        user_token_client = mocker.Mock()
        user_token_client.user_token.get_token = pytest.AsyncMock(return_value=TokenResponse())

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=active_flow_state
        )
        flow_response = await flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining - 1 == flow_response.flow_state.attempts_remaining
        assert not flow_response.token_response.token
        if active_flow_state.attempts_remaining == 1:
            assert flow_response.flow_state.tag == FlowStateTag.FAILURE
        else:
            assert flow_response.flow_state.tag == FlowStateTag.CONTINUE
        assert flow_response.flow_error_tag == FlowErrorTag.UNKNOWN
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            magic_code="987654"
        )

    @pytest.mark.asyncio
    async def test_continue_flow_invoke_token_exchange(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.name = "signin/exchangeState"
        turn_context.activity.value = "request_body"
        user_token_client = mocker.Mock()
        user_token_client.user_token.exchange_token = pytest.AsyncMock(return_value=TokenResponse(token="exchange-token"))

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=active_flow_state
        )
        flow_response = await flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining == flow_response.flow_state.attempts_remaining
        assert flow_response.token_response.token == "exchange-token"
        assert flow_response.flow_state.tag == FlowStateTag.COMPLETE
        assert flow_response.flow_error_tag == FlowErrorTag.NONE
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            body="request_body"
        )

    @pytest.mark.asyncio
    async def test_continue_flow_invoke_token_exchange_no_token(self, mocker, turn_context, active_flow_state):
        # mock
        turn_context.activity.type = ActivityTypes.message
        turn_context.activity.name = "signin/exchangeState"
        turn_context.activity.value = "request_body"
        user_token_client = mocker.Mock()
        user_token_client.user_token.exchange_token = pytest.AsyncMock(return_value=TokenResponse())

        # test
        flow = AuthFlow(
            abs_oauth_connection_name="test_connection",
            user_token_client=user_token_client,
            flow_state=active_flow_state
        )
        flow_response = await flow.continue_flow(turn_context)

        # verify
        assert active_flow_state.attempts_remaining - 1 == flow_response.flow_state.attempts_remaining
        assert not flow_response.token_response
        if active_flow_state.attempts_remaining == 1:
            assert flow_response.flow_state.tag == FlowStateTag.FAILURE
        else:
            assert flow_response.flow_state.tag == FlowStateTag.CONTINUE
        assert flow_response.flow_error_tag == FlowErrorTag.UNKNOWN
        assert user_token_client.user_token.get_token.called_once_with(
            user_id="__user_id",
            connection_name="test_connection",
            channel_id="__channel_id",
            body="request_body"
        )

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow(self):
        assert True # robrandao: TODO