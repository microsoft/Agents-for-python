import pytest

from microsoft_agents.activity import (
    ActivityTypes,
    TokenResponse,
    SignInResource,
    TokenExchangeState,
)
from microsoft_agents.hosting.core.oauth import (
    OAuthFlow,
    FlowErrorTag,
    FlowStateTag,
    FlowResponse,
)

# test constants
from .tools.testing_oauth import *

from tests._common import (
    SDKFixtures,
    TestingEnvironment,
    TestingUserTokenClientMixin,
    TestingActivityMixin,
    TEST_DEFAULTS
)

DEFAULTS = TEST_DEFAULTS()

class OAuthFlowTestEnv(TestingEnvironment, TestingUserTokenClientMixin, TestingActivityMixin):

    def mock_TokenExchangeState(self, mocker, get_encoded_value_return):
        mocker.patch.object(
            TokenExchangeState, "get_encoded_state", return_value=get_encoded_value_return
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


class TestOAuthFlow(SDKFixtures[OAuthFlowTestEnv]):

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
        expected_final_flow_state.tag = FlowStateTag.COMPLETE

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
    async def test_get_user_token_failure(self, testenv, mocker, sample_flow_state):
        # setup
        user_token_client = testenv.UserTokenClient(mocker, get_token_return=None)
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
        self, mocker, sample_flow_state, user_token_client, activity
    ):
        # setup
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_flow_state = sample_flow_state
        expected_flow_state.user_token = DEFAULTS.token
        expected_flow_state.tag = FlowStateTag.COMPLETE

        # test
        response = await flow.begin_flow(activity)

        # verify
        flow_state = flow.flow_state
        expected_flow_state.expiration = flow_state.expiration
        assert flow_state == expected_flow_state

        assert response.flow_state == flow_state
        assert response.sign_in_resource is None  # No sign-in resource in this case
        assert response.flow_error_tag == FlowErrorTag.NONE
        assert response.token_response.token == DEFAULTS.token
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=DEFAULTS.user_id,
            connection_name=DEFAULTS.abs_oauth_connection_name,
            channel_id=DEFAULTS.channel_id,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_begin_flow_long_case(
        self, testenv, mocker, sample_flow_state, activity
    ):
        # resources
        dummy_sign_in_resource = SignInResource(
            sign_in_link="https://example.com/signin",
            token_exchange_state=testenv.TokenExchangeState(mocker, get_encoded_state_return="encoded_state")
        )
        user_token_client = testenv.UserTokenClient(
            mocker,
            get_token_return=TokenResponse(),
            get_sign_in_resource_return=dummy_sign_in_resource
        )

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
        self, mocker, sample_inactive_flow_state, user_token_client, activity
    ):
        # setup
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
        expected_flow_state.user_token = DEFAULTS.token
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
        assert flow_response.token_response == TokenResponse(token=DEFAULTS.token)
        assert flow_response.flow_error_tag == FlowErrorTag.NONE

    @pytest.mark.asyncio
    @pytest.mark.parametrize("magic_code", ["magic", "123", "", "1239453"])
    async def test_continue_flow_active_message_magic_format_error(
        self, testenv, mocker, sample_active_flow_state, user_token_client, magic_code
    ):
        # setup
        activity = testenv.Activity(mocker, type=ActivityTypes.message, text=magic_code)
        await self.helper_continue_flow_failure(
            sample_active_flow_state,
            user_token_client,
            activity,
            FlowErrorTag.MAGIC_FORMAT,
        )
        user_token_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_continue_flow_active_message_magic_code_error(
        self, testenv, mocker, sample_active_flow_state
    ):
        # setup
        user_token_client = testenv.UserTokenClient(get_token_return=TokenResponse())
        activity = self.Activity(mocker, type=ActivityTypes.message, text="123456")
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
        activity = self.Activity(mocker, ActivityTypes.message, text="123456")
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
        self, testenv, mocker, sample_active_flow_state
    ):
        # setup
        user_token_client = testenv.UserTokenClient(get_token_return=TokenResponse())
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
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
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
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
        self, testenv, mocker, sample_active_flow_state
    ):
        token_exchange_request = {}
        user_token_client = testenv.UserTokenClient(mocker, exchange_token_return=TokenResponse())
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
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
        self, testenv, mocker, sample_active_flow_state
    ):
        token_exchange_request = {}
        user_token_client = testenv.UserTokenClient(mocker, token_exchange_return=TokenResponse(token=DEFAULTS.token))
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
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
            activity = self.Activity(
                mocker, type=ActivityTypes.invoke, name="other", value={}
            )
            flow = OAuthFlow(sample_active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_continue_flow_invalid_activity_type(
        self, mocker, sample_active_flow_state, user_token_client
    ):
        with pytest.raises(ValueError):
            activity = self.Activity(
                mocker,type=ActivityTypes.command, name="other", value={}
            )
            flow = OAuthFlow(sample_active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_not_started_flow(self, mocker, activity):
        # setup
        sample_flow_state = FLOW_STATES.NOT_STARTED_FLOW.model_copy()
        expected_response = FlowResponse(
            flow_state=sample_flow_state,
            token_response=TokenResponse(token=sample_flow_state.user_token),
        )
        mocker.patch.object(OAuthFlow, "begin_flow", return_value=expected_response)

        flow = OAuthFlow(sample_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        OAuthFlow.begin_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_inactive_flow(
        self,
        mocker,
        sample_inactive_flow_state_not_completed,
        activity
    ):
        # setup
        expected_response = FlowResponse(
            flow_state=sample_inactive_flow_state_not_completed,
            token_response=TokenResponse(),
        )
        mocker.patch.object(OAuthFlow, "begin_flow", return_value=expected_response)

        flow = OAuthFlow(sample_inactive_flow_state_not_completed, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        OAuthFlow.begin_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_active_flow(
        self,
        mocker,
        sample_active_flow_state,
        activity
    ):
        # setup
        expected_response = FlowResponse(
            flow_state=sample_active_flow_state,
            token_response=TokenResponse(token=sample_active_flow_state.user_token),
        )
        mocker.patch.object(OAuthFlow, "continue_flow", return_value=expected_response)

        flow = OAuthFlow(sample_active_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        OAuthFlow.continue_flow.assert_called_once_with(activity)

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
