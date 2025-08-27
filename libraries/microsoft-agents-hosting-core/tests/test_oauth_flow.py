import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    TokenResponse,
    SignInResource,
    TokenExchangeState,
    ConversationReference,
    ChannelAccount,
)
from microsoft_agents.hosting.core.oauth import (
    OAuthFlow,
    FlowErrorTag,
    FlowStateTag,
    FlowResponse,
)
from microsoft_agents.hosting.core.connector.user_token_base import UserTokenBase
from microsoft_agents.hosting.core.connector.user_token_client_base import (
    UserTokenClientBase,
)

# test constants
from .tools.testing_oauth import *


class TestOAuthFlowUtils:

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
        return self.create_user_token_client(mocker, get_token_return=RES_TOKEN)

    def create_activity(
        self,
        mocker,
        activity_type=ActivityTypes.message,
        name="a",
        value=None,
        text="a",
    ):
        # def conv_ref():
        #     return mocker.MagicMock(spec=ConversationReference)
        mock_conversation_ref = mocker.MagicMock(ConversationReference)
        mocker.patch.object(
            Activity,
            "get_conversation_reference",
            return_value=mocker.MagicMock(ConversationReference),
        )
        # mocker.patch.object(ConversationReference, "create", return_value=conv_ref())
        return Activity(
            type=activity_type,
            name=name,
            from_property=ChannelAccount(id=USER_ID),
            channel_id=CHANNEL_ID,
            # get_conversation_reference=mocker.Mock(return_value=conv_ref),
            relates_to=mocker.MagicMock(ConversationReference),
            value=value,
            text=text,
        )

    @pytest.fixture(params=FLOW_STATES.ALL())
    def sample_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.FAILED())
    def sample_failed_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.INACTIVE())
    def sample_inactive_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(
        params=[
            flow_state
            for flow_state in FLOW_STATES.INACTIVE()
            if flow_state.tag != FlowStateTag.COMPLETE
        ]
    )
    def sample_inactive_flow_state_not_completed(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.ACTIVE())
    def sample_active_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture
    def flow(self, sample_flow_state, user_token_client):
        return OAuthFlow(sample_flow_state, user_token_client)


class TestOAuthFlow(TestOAuthFlowUtils):

    def test_init_no_user_token_client(self, sample_flow_state):
        with pytest.raises(ValueError):
            OAuthFlow(sample_flow_state, None)

    @pytest.mark.parametrize(
        "missing_value", ["connection", "ms_app_id", "channel_id", "user_id"]
    )
    def test_init_errors(self, missing_value, user_token_client):
        flow_state = FLOW_STATES.STARTED_FLOW.model_copy()
        flow_state.__setattr__(missing_value, None)
        with pytest.raises(ValueError):
            OAuthFlow(flow_state, user_token_client)
        flow_state.__setattr__(missing_value, "")
        with pytest.raises(ValueError):
            OAuthFlow(flow_state, user_token_client)

    def test_init_with_state(self, sample_flow_state, user_token_client):
        flow = OAuthFlow(sample_flow_state, user_token_client)
        assert flow.flow_state == sample_flow_state

    def test_flow_state_prop_copy(self, flow):
        flow_state = flow.flow_state
        flow_state.user_id = flow_state.user_id + "_copy"
        assert flow.flow_state.user_id == USER_ID
        assert flow_state.user_id == f"{USER_ID}_copy"

    @pytest.mark.asyncio
    async def test_get_user_token_success(self, sample_flow_state, user_token_client):
        # setup
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_final_flow_state = sample_flow_state
        expected_final_flow_state.user_token = RES_TOKEN

        # test
        token_response = await flow.get_user_token()
        token = token_response.token

        # verify
        assert token == RES_TOKEN
        expected_final_flow_state.expiration = flow.flow_state.expiration
        assert flow.flow_state == expected_final_flow_state
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=USER_ID,
            connection_name=ABS_OAUTH_CONNECTION_NAME,
            channel_id=CHANNEL_ID,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_get_user_token_failure(self, mocker, sample_flow_state):
        # setup
        user_token_client = self.create_user_token_client(mocker, get_token_return=None)
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_final_flow_state = flow.flow_state

        # test
        token_response = await flow.get_user_token()

        # verify
        assert token_response == TokenResponse()
        assert flow.flow_state == expected_final_flow_state
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=USER_ID,
            connection_name=ABS_OAUTH_CONNECTION_NAME,
            channel_id=CHANNEL_ID,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_sign_out(self, sample_flow_state, user_token_client):
        # setup
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_flow_state = sample_flow_state
        expected_flow_state.user_token = ""
        expected_flow_state.tag = FlowStateTag.NOT_STARTED

        # test
        await flow.sign_out()

        # verify
        user_token_client.user_token.sign_out.assert_called_once_with(
            user_id=USER_ID,
            connection_name=ABS_OAUTH_CONNECTION_NAME,
            channel_id=CHANNEL_ID,
        )
        assert flow.flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_begin_flow_easy_case(
        self, mocker, sample_flow_state, user_token_client
    ):
        # setup
        flow = OAuthFlow(sample_flow_state, user_token_client)
        activity = mocker.Mock(spec=Activity)
        expected_flow_state = sample_flow_state
        expected_flow_state.user_token = RES_TOKEN

        # test
        response = await flow.begin_flow(activity)

        # verify
        flow_state = flow.flow_state
        expected_flow_state.expiration = flow_state.expiration
        assert flow_state == expected_flow_state

        assert response.flow_state == flow_state
        assert response.sign_in_resource is None  # No sign-in resource in this case
        assert response.flow_error_tag == FlowErrorTag.NONE
        assert response.token_response.token == RES_TOKEN
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=USER_ID,
            connection_name=ABS_OAUTH_CONNECTION_NAME,
            channel_id=CHANNEL_ID,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_begin_flow_long_case(
        self, mocker, sample_flow_state, user_token_client
    ):
        # mock
        # tes = mocker.Mock(TokenExchangeState)
        # tes.get_encoded_state = mocker.Mock(return_value="encoded_state")
        mocker.patch.object(
            TokenExchangeState, "get_encoded_state", return_value="encoded_state"
        )
        dummy_sign_in_resource = SignInResource(
            sign_in_link="https://example.com/signin",
            token_exchange_state=mocker.Mock(
                TokenExchangeState,
                get_encoded_state=mocker.Mock(return_value="encoded_state"),
            ),
        )
        user_token_client.user_token.get_token = mocker.AsyncMock(
            return_value=TokenResponse()
        )
        user_token_client.agent_sign_in.get_sign_in_resource = mocker.AsyncMock(
            return_value=dummy_sign_in_resource
        )
        activity = self.create_activity(mocker)

        # setup
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_flow_state = sample_flow_state
        expected_flow_state.user_token = ""
        expected_flow_state.tag = FlowStateTag.BEGIN
        expected_flow_state.attempts_remaining = 3
        expected_flow_state.continuation_activity = activity

        # test
        response = await flow.begin_flow(activity)

        # verify flow_state
        flow_state = flow.flow_state
        expected_flow_state.expiration = (
            flow_state.expiration
        )  # robrandao: TODO -> ignore this for now
        assert flow_state == response.flow_state
        assert flow_state == expected_flow_state

        # verify FlowResponse
        assert response.sign_in_resource == dummy_sign_in_resource
        assert response.flow_error_tag == FlowErrorTag.NONE
        assert not response.token_response
        # robrandao: TODO more assertions on sign_in_resource

    @pytest.mark.asyncio
    async def test_continue_flow_not_active(
        self, mocker, sample_inactive_flow_state, user_token_client
    ):
        # setup
        activity = mocker.Mock()
        flow = OAuthFlow(sample_inactive_flow_state, user_token_client)
        expected_flow_state = sample_inactive_flow_state
        expected_flow_state.tag = FlowStateTag.FAILURE

        # test
        flow_response = await flow.continue_flow(activity)
        flow_state = flow.flow_state

        # verify
        assert flow_state == expected_flow_state
        assert flow_response.flow_state == flow_state
        assert not flow_response.token_response

    async def helper_continue_flow_failure(
        self, active_flow_state, user_token_client, activity, flow_error_tag
    ):
        # setup
        flow = OAuthFlow(active_flow_state, user_token_client)
        expected_flow_state = active_flow_state
        expected_flow_state.tag = (
            FlowStateTag.CONTINUE
            if active_flow_state.attempts_remaining > 1
            else FlowStateTag.FAILURE
        )
        expected_flow_state.attempts_remaining = (
            active_flow_state.attempts_remaining - 1
        )

        # test
        flow_response = await flow.continue_flow(activity)
        flow_state = flow.flow_state

        # verify
        assert flow_response.flow_state == flow_state
        assert expected_flow_state == flow_state
        assert flow_response.token_response == TokenResponse()
        assert flow_response.flow_error_tag == flow_error_tag

    async def helper_continue_flow_success(
        self, active_flow_state, user_token_client, activity
    ):
        # setup
        flow = OAuthFlow(active_flow_state, user_token_client)
        expected_flow_state = active_flow_state
        expected_flow_state.tag = FlowStateTag.COMPLETE
        expected_flow_state.user_token = RES_TOKEN
        expected_flow_state.attempts_remaining = active_flow_state.attempts_remaining

        # test
        flow_response = await flow.continue_flow(activity)
        flow_state = flow.flow_state
        expected_flow_state.expiration = (
            flow_state.expiration
        )  # robrandao: TODO -> ignore this for now

        # verify
        assert flow_response.flow_state == flow_state
        assert expected_flow_state == flow_state
        assert flow_response.token_response == TokenResponse(token=RES_TOKEN)
        assert flow_response.flow_error_tag == FlowErrorTag.NONE

    @pytest.mark.asyncio
    @pytest.mark.parametrize("magic_code", ["magic", "123", "", "1239453"])
    async def test_continue_flow_active_message_magic_format_error(
        self, mocker, sample_active_flow_state, user_token_client, magic_code
    ):
        # setup
        activity = self.create_activity(mocker, ActivityTypes.message, text=magic_code)
        await self.helper_continue_flow_failure(
            sample_active_flow_state,
            user_token_client,
            activity,
            FlowErrorTag.MAGIC_FORMAT,
        )
        user_token_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_continue_flow_active_message_magic_code_error(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        # setup
        user_token_client.user_token.get_token = mocker.AsyncMock(
            return_value=TokenResponse()
        )
        activity = self.create_activity(mocker, ActivityTypes.message, text="123456")
        await self.helper_continue_flow_failure(
            sample_active_flow_state,
            user_token_client,
            activity,
            FlowErrorTag.MAGIC_CODE_INCORRECT,
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            code="123456",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_message_success(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        # setup
        activity = self.create_activity(mocker, ActivityTypes.message, text="123456")
        await self.helper_continue_flow_success(
            sample_active_flow_state, user_token_client, activity
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            code="123456",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_verify_state_error(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        # setup
        user_token_client.user_token.get_token = mocker.AsyncMock(
            return_value=TokenResponse()
        )
        activity = self.create_activity(
            mocker,
            ActivityTypes.invoke,
            name="signin/verifyState",
            value={"state": "magic_code"},
        )
        await self.helper_continue_flow_failure(
            sample_active_flow_state, user_token_client, activity, FlowErrorTag.OTHER
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            code="magic_code",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_verify_success(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        activity = self.create_activity(
            mocker,
            ActivityTypes.invoke,
            name="signin/verifyState",
            value={"state": "magic_code"},
        )
        await self.helper_continue_flow_success(
            sample_active_flow_state, user_token_client, activity
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            code="magic_code",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_token_exchange_error(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        token_exchange_request = {}
        user_token_client.user_token.exchange_token = mocker.AsyncMock(
            return_value=TokenResponse()
        )
        activity = self.create_activity(
            mocker,
            ActivityTypes.invoke,
            name="signin/tokenExchange",
            value=token_exchange_request,
        )
        await self.helper_continue_flow_failure(
            sample_active_flow_state, user_token_client, activity, FlowErrorTag.OTHER
        )
        user_token_client.user_token.exchange_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            body=token_exchange_request,
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_token_exchange_success(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        token_exchange_request = {}
        user_token_client.user_token.exchange_token = mocker.AsyncMock(
            return_value=TokenResponse(token=RES_TOKEN)
        )
        activity = self.create_activity(
            mocker,
            ActivityTypes.invoke,
            name="signin/tokenExchange",
            value=token_exchange_request,
        )
        await self.helper_continue_flow_success(
            sample_active_flow_state, user_token_client, activity
        )
        user_token_client.user_token.exchange_token.assert_called_once_with(
            user_id=sample_active_flow_state.user_id,
            connection_name=sample_active_flow_state.connection,
            channel_id=sample_active_flow_state.channel_id,
            body=token_exchange_request,
        )

    @pytest.mark.asyncio
    async def test_continue_flow_invalid_invoke_name(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        with pytest.raises(ValueError):
            activity = self.create_activity(
                mocker, ActivityTypes.invoke, name="other", value={}
            )
            flow = OAuthFlow(sample_active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_continue_flow_invalid_activity_type(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        with pytest.raises(ValueError):
            activity = self.create_activity(
                mocker, ActivityTypes.command, name="other", value={}
            )
            flow = OAuthFlow(sample_active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_not_started_flow(self, mocker):
        # setup
        sample_flow_state = FLOW_STATES.NOT_STARTED_FLOW.model_copy()
        expected_response = FlowResponse(
            flow_state=sample_flow_state,
            token_response=TokenResponse(token=sample_flow_state.user_token),
        )
        mocker.patch.object(OAuthFlow, "begin_flow", return_value=expected_response)

        activity_mock = mocker.Mock()
        flow = OAuthFlow(sample_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity_mock)

        # verify
        assert actual_response is expected_response
        OAuthFlow.begin_flow.assert_called_once_with(activity_mock)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_inactive_flow(
        self,
        mocker,
        sample_inactive_flow_state_not_completed,
    ):
        # setup
        expected_response = FlowResponse(
            flow_state=sample_inactive_flow_state_not_completed,
            token_response=TokenResponse(),
        )
        mocker.patch.object(OAuthFlow, "begin_flow", return_value=expected_response)

        flow = OAuthFlow(sample_inactive_flow_state_not_completed, mocker.Mock())

        # test
        activity_mock = mocker.Mock()
        actual_response = await flow.begin_or_continue_flow(activity_mock)

        # verify
        assert actual_response is expected_response
        OAuthFlow.begin_flow.assert_called_once_with(activity_mock)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_active_flow(
        self,
        mocker,
        sample_active_flow_state,
    ):
        # setup
        expected_response = FlowResponse(
            flow_state=sample_active_flow_state,
            token_response=TokenResponse(token=sample_active_flow_state.user_token),
        )
        mocker.patch.object(OAuthFlow, "continue_flow", return_value=expected_response)

        flow = OAuthFlow(sample_active_flow_state, mocker.Mock())

        # test
        activity_mock = mocker.Mock()
        actual_response = await flow.begin_or_continue_flow(activity_mock)

        # verify
        assert actual_response is expected_response
        OAuthFlow.continue_flow.assert_called_once_with(activity_mock)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_stale_flow_state(self, mocker):
        flow_state = FLOW_STATES.ACTIVE_EXP_FLOW.model_copy()
        expected_response = FlowResponse()

        mocker.patch.object(OAuthFlow, "begin_flow", return_value=expected_response)

        flow = OAuthFlow(flow_state, mocker.Mock())
        actual_response = await flow.begin_or_continue_flow(None)

        assert actual_response is expected_response
        OAuthFlow.begin_flow.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_completed_flow_state(self, mocker):
        flow_state = FLOW_STATES.COMPLETED_FLOW.model_copy()
        expected_response = FlowResponse(
            flow_state=flow_state,
            token_response=TokenResponse(token=flow_state.user_token),
        )
        mocker.patch.object(OAuthFlow, "begin_flow", return_value=None)
        mocker.patch.object(OAuthFlow, "continue_flow", return_value=None)

        flow = OAuthFlow(flow_state, mocker.Mock())
        actual_response = await flow.begin_or_continue_flow(None)

        assert actual_response == expected_response
        OAuthFlow.begin_flow.assert_not_called()
        OAuthFlow.continue_flow.assert_not_called()
