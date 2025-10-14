import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    TokenResponse,
    SignInResource,
    TokenExchangeState,
    ConversationReference,
)
from microsoft_agents.hosting.core._oauth import (
    _OAuthFlow,
    _FlowErrorTag,
    _FlowStateTag,
    _FlowResponse,
)

from tests._common.data import DEFAULT_TEST_VALUES, FLOW_TEST_DATA
from tests._common.data.storage_test_data import STORAGE_TEST_DATA
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import mock_UserTokenClient

DEFAULTS = DEFAULT_TEST_VALUES()
FLOW_DATA = FLOW_TEST_DATA()


def create_testing_Activity(
    mocker,
    type=ActivityTypes.message,
    name="a",
    value=None,
    text="a",
):
    # mock_conversation_ref = mocker.MagicMock(ConversationReference)
    mocker.patch.object(
        Activity,
        "get_conversation_reference",
        return_value=mocker.MagicMock(ConversationReference),
    )
    return Activity(
        type=type,
        name=name,
        from_property=ChannelAccount(id=DEFAULTS.user_id),
        channel_id=DEFAULTS.channel_id,
        # get_conversation_reference=mocker.Mock(return_value=conv_ref),
        relates_to=mocker.MagicMock(ConversationReference),
        value=value,
        text=text,
    )


class TestUtils(FlowStateFixtures):
    def setup_method(self):
        self.UserTokenClient = mock_UserTokenClient
        self.Activity = create_testing_Activity

    @pytest.fixture
    def user_token_client(self, mocker):
        return self.UserTokenClient(mocker, get_token_return=DEFAULTS.token)

    @pytest.fixture
    def activity(self, mocker):
        return self.Activity(mocker)

    @pytest.fixture
    def flow(self, flow_state, user_token_client):
        return _OAuthFlow(flow_state, user_token_client)


class TestOAuthFlow(TestUtils):
    def test_init_no_user_token_client(self, flow_state):
        with pytest.raises(ValueError):
            _OAuthFlow(flow_state, None)

    @pytest.mark.parametrize(
        "missing_value", ["connection", "ms_app_id", "channel_id", "user_id"]
    )
    def test_init_errors(self, missing_value, user_token_client):
        started_flow_state = FLOW_DATA.started.model_copy()
        flow_state = started_flow_state
        flow_state.__setattr__(missing_value, None)
        with pytest.raises(ValueError):
            _OAuthFlow(flow_state, user_token_client)
        flow_state.__setattr__(missing_value, "")
        with pytest.raises(ValueError):
            _OAuthFlow(flow_state, user_token_client)

    def test_init_with_state(self, flow_state, user_token_client):
        flow = _OAuthFlow(flow_state, user_token_client)
        assert flow.flow_state == flow_state

    def test_flow_state_prop_copy(self, flow):
        flow_state = flow.flow_state
        flow_state.user_id = flow_state.user_id + "_copy"
        assert flow.flow_state.user_id == flow.flow_state.user_id
        assert flow_state.user_id == f"{flow.flow_state.user_id}_copy"

    @pytest.mark.asyncio
    async def test_get_user_token_success(self, flow_state, user_token_client):
        # setup
        flow = _OAuthFlow(flow_state, user_token_client)
        expected_final_flow_state = flow_state
        expected_final_flow_state.tag = _FlowStateTag.COMPLETE

        # test
        token_response = await flow.get_user_token()

        # verify
        token = token_response.token
        assert token == DEFAULTS.token
        expected_final_flow_state.expiration = flow.flow_state.expiration
        assert flow.flow_state == expected_final_flow_state
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=flow_state.user_id,
            connection_name=flow_state.connection,
            channel_id=flow_state.channel_id,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_get_user_token_failure(self, mocker, flow_state):
        # setup
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse()
        )
        flow = _OAuthFlow(flow_state, user_token_client)
        expected_final_flow_state = flow.flow_state

        # test
        token_response = await flow.get_user_token()

        # verify
        assert token_response == TokenResponse()
        assert flow.flow_state == expected_final_flow_state
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=flow_state.user_id,
            connection_name=flow_state.connection,
            channel_id=flow_state.channel_id,
            code=None,
        )

    @pytest.mark.asyncio
    async def test_sign_out(self, flow_state, user_token_client):
        # setup
        flow = _OAuthFlow(flow_state, user_token_client)
        expected_flow_state = flow_state
        expected_flow_state.tag = _FlowStateTag.NOT_STARTED

        # test
        await flow.sign_out()

        # verify
        user_token_client.user_token.sign_out.assert_called_once_with(
            user_id=flow_state.user_id,
            connection_name=flow_state.connection,
            channel_id=flow_state.channel_id,
        )
        assert flow.flow_state == expected_flow_state

    @pytest.mark.asyncio
    async def test_begin_flow_easy_case(self, mocker, flow_state, activity):
        # setup
        # user_token_client = self.UserTokenClient(
        #     mocker, get_token_return=TokenResponse(token=DEFAULTS.token)
        # )
        user_token_client = self.UserTokenClient(
            mocker,
            get_token_or_sign_in_resource_return=TokenResponse(token=DEFAULTS.token),
        )
        mocker.patch.object(
            TokenExchangeState, "get_encoded_state", return_value="encoded_state"
        )
        flow = _OAuthFlow(flow_state, user_token_client)
        expected_flow_state = flow_state
        expected_flow_state.tag = _FlowStateTag.COMPLETE

        # test
        response = await flow.begin_flow(activity)

        # verify
        out_flow_state = flow.flow_state
        expected_flow_state.expiration = out_flow_state.expiration
        assert out_flow_state == expected_flow_state

        assert response.flow_state == out_flow_state
        assert response.sign_in_resource is None  # No sign-in resource in this case
        assert response.flow_error_tag == _FlowErrorTag.NONE
        assert response.token_response
        assert response.token_response.token == DEFAULTS.token
        user_token_client.user_token._get_token_or_sign_in_resource.assert_called_once_with(
            activity.from_property.id,
            flow_state.connection,
            activity.channel_id,
            "encoded_state",
        )

    @pytest.mark.asyncio
    async def test_begin_flow_long_case(self, mocker, flow_state, activity):
        # resources
        mocker.patch.object(
            TokenExchangeState, "get_encoded_state", return_value="encoded_state"
        )
        dummy_sign_in_resource = SignInResource(
            sign_in_link="https://example.com/signin",
        )
        user_token_client = self.UserTokenClient(
            mocker, get_token_or_sign_in_resource_return=dummy_sign_in_resource
        )

        # setup
        flow = _OAuthFlow(flow_state, user_token_client)
        expected_flow_state = flow_state
        expected_flow_state.tag = _FlowStateTag.BEGIN
        expected_flow_state.attempts_remaining = 3

        # test
        response = await flow.begin_flow(activity)

        # verify flow_state
        out_flow_state = flow.flow_state
        expected_flow_state.expiration = (
            out_flow_state.expiration
        )  # robrandao: TODO -> ignore this for now
        assert out_flow_state == response.flow_state
        assert out_flow_state == expected_flow_state

        # verify _FlowResponse
        assert response.sign_in_resource == dummy_sign_in_resource
        assert response.flow_error_tag == _FlowErrorTag.NONE
        assert not response.token_response
        # robrandao: TODO more assertions on sign_in_resource

    @pytest.mark.asyncio
    async def test_continue_flow_not_active(
        self, inactive_flow_state, user_token_client, activity
    ):
        # setup
        flow = _OAuthFlow(inactive_flow_state, user_token_client)
        expected_flow_state = inactive_flow_state
        expected_flow_state.tag = _FlowStateTag.FAILURE

        # test
        flow_response = await flow.continue_flow(activity)
        out_flow_state = flow.flow_state

        # verify
        assert out_flow_state == expected_flow_state
        assert flow_response.flow_state == out_flow_state
        assert not flow_response.token_response

    async def helper_continue_flow_failure(
        self, active_flow_state, user_token_client, activity, flow_error_tag
    ):
        # setup
        flow = _OAuthFlow(active_flow_state, user_token_client)
        expected_flow_state = active_flow_state
        expected_flow_state.tag = (
            _FlowStateTag.CONTINUE
            if active_flow_state.attempts_remaining > 1
            else _FlowStateTag.FAILURE
        )
        expected_flow_state.attempts_remaining = (
            active_flow_state.attempts_remaining - 1
        )

        # test
        flow_response = await flow.continue_flow(activity)
        out_flow_state = flow.flow_state

        # verify
        assert flow_response.flow_state == out_flow_state
        assert expected_flow_state == out_flow_state
        assert flow_response.token_response == TokenResponse()
        assert flow_response.flow_error_tag == flow_error_tag

    async def helper_continue_flow_success(
        self, active_flow_state, user_token_client, activity, expected_token
    ):
        # setup
        flow = _OAuthFlow(active_flow_state, user_token_client)
        expected_flow_state = active_flow_state
        expected_flow_state.tag = _FlowStateTag.COMPLETE
        expected_flow_state.attempts_remaining = active_flow_state.attempts_remaining

        # test
        flow_response = await flow.continue_flow(activity)
        out_flow_state = flow.flow_state
        expected_flow_state.expiration = (
            out_flow_state.expiration
        )  # robrandao: TODO -> ignore this for now

        # verify
        assert flow_response.flow_state == out_flow_state
        assert expected_flow_state == out_flow_state
        assert flow_response.token_response == TokenResponse(token=expected_token)
        assert flow_response.flow_error_tag == _FlowErrorTag.NONE

    @pytest.mark.asyncio
    @pytest.mark.parametrize("magic_code", ["magic", "123", "", "1239453"])
    async def test_continue_flow_active_message_magic_format_error(
        self, mocker, active_flow_state, user_token_client, magic_code
    ):
        # setup
        activity = self.Activity(mocker, type=ActivityTypes.message, text=magic_code)
        await self.helper_continue_flow_failure(
            active_flow_state,
            user_token_client,
            activity,
            _FlowErrorTag.MAGIC_FORMAT,
        )
        user_token_client.user_token.get_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_continue_flow_active_message_magic_code_error(
        self, mocker, active_flow_state
    ):
        # setup
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse()
        )
        activity = self.Activity(mocker, type=ActivityTypes.message, text="123456")
        await self.helper_continue_flow_failure(
            active_flow_state,
            user_token_client,
            activity,
            _FlowErrorTag.MAGIC_CODE_INCORRECT,
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            code="123456",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_message_success(
        self, mocker, active_flow_state, user_token_client
    ):
        # setup
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse(token=DEFAULTS.token)
        )
        activity = self.Activity(mocker, ActivityTypes.message, text="123456")
        await self.helper_continue_flow_success(
            active_flow_state,
            user_token_client,
            activity,
            expected_token=DEFAULTS.token,
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            code="123456",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_verify_state_error(
        self, mocker, active_flow_state
    ):
        # setup
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse()
        )
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
            name="signin/verifyState",
            value={"state": "magic_code"},
        )
        await self.helper_continue_flow_failure(
            active_flow_state, user_token_client, activity, _FlowErrorTag.OTHER
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            code="magic_code",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_verify_success(
        self,
        mocker,
        active_flow_state,
    ):
        user_token_client = self.UserTokenClient(
            mocker, get_token_return=TokenResponse(token=DEFAULTS.token)
        )
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
            name="signin/verifyState",
            value={"state": "magic_code"},
        )
        await self.helper_continue_flow_success(
            active_flow_state,
            user_token_client,
            activity,
            expected_token=DEFAULTS.token,
        )
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            code="magic_code",
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_token_exchange_error(
        self, mocker, active_flow_state
    ):
        token_exchange_request = {}
        user_token_client = self.UserTokenClient(
            mocker, exchange_token_return=TokenResponse()
        )
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
            name="signin/tokenExchange",
            value=token_exchange_request,
        )
        await self.helper_continue_flow_failure(
            active_flow_state, user_token_client, activity, _FlowErrorTag.OTHER
        )
        user_token_client.user_token.exchange_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            body=token_exchange_request,
        )

    @pytest.mark.asyncio
    async def test_continue_flow_active_sign_in_token_exchange_success(
        self, mocker, active_flow_state
    ):
        token_exchange_request = {}
        user_token_client = self.UserTokenClient(
            mocker, exchange_token_return=TokenResponse(token=DEFAULTS.token)
        )
        activity = self.Activity(
            mocker,
            type=ActivityTypes.invoke,
            name="signin/tokenExchange",
            value=token_exchange_request,
        )
        await self.helper_continue_flow_success(
            active_flow_state,
            user_token_client,
            activity,
            expected_token=DEFAULTS.token,
        )
        user_token_client.user_token.exchange_token.assert_called_once_with(
            user_id=active_flow_state.user_id,
            connection_name=active_flow_state.connection,
            channel_id=active_flow_state.channel_id,
            body=token_exchange_request,
        )

    @pytest.mark.asyncio
    async def test_continue_flow_invalid_invoke_name(
        self, mocker, active_flow_state, user_token_client
    ):
        with pytest.raises(ValueError):
            activity = self.Activity(
                mocker, type=ActivityTypes.invoke, name="other", value={}
            )
            flow = _OAuthFlow(active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_continue_flow_invalid_activity_type(
        self, mocker, active_flow_state, user_token_client
    ):
        with pytest.raises(ValueError):
            activity = self.Activity(
                mocker, type=ActivityTypes.command, name="other", value={}
            )
            flow = _OAuthFlow(active_flow_state, user_token_client)
            await flow.continue_flow(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_not_started_flow(
        self,
        mocker,
        activity,
    ):
        # setup
        not_started_flow_state = FLOW_DATA.not_started.model_copy()
        expected_response = _FlowResponse(
            flow_state=not_started_flow_state,
            token_response=TokenResponse(),
        )
        mocker.patch.object(_OAuthFlow, "begin_flow", return_value=expected_response)

        flow = _OAuthFlow(not_started_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        _OAuthFlow.begin_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_inactive_flow(
        self, mocker, inactive_flow_state_not_completed, activity
    ):
        # mock
        expected_response = _FlowResponse(
            flow_state=inactive_flow_state_not_completed,
            token_response=TokenResponse(),
        )
        mocker.patch.object(_OAuthFlow, "begin_flow", return_value=expected_response)

        # setup
        flow = _OAuthFlow(inactive_flow_state_not_completed, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        _OAuthFlow.begin_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_active_flow(
        self, mocker, active_flow_state, activity, user_token_client
    ):
        # mock
        expected_response = _FlowResponse(
            flow_state=active_flow_state,
            token_response=TokenResponse(token=DEFAULTS.token),
        )
        mocker.patch.object(_OAuthFlow, "continue_flow", return_value=expected_response)

        # setup
        flow = _OAuthFlow(active_flow_state, user_token_client)

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        _OAuthFlow.continue_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_stale_flow_state(
        self,
        mocker,
        activity,
    ):
        # mock
        expired_flow_state = FLOW_DATA.active_exp.model_copy()
        expected_response = _FlowResponse()
        mocker.patch.object(_OAuthFlow, "begin_flow", return_value=expected_response)

        # setup
        flow = _OAuthFlow(expired_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response is expected_response
        _OAuthFlow.begin_flow.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_begin_or_continue_flow_completed_flow_state(self, mocker, activity):
        completed_flow_state = FLOW_DATA.completed.model_copy()
        # mock
        expected_response = _FlowResponse(
            flow_state=completed_flow_state,
            token_response=TokenResponse(token="some-token"),
        )
        mocker.patch.object(_OAuthFlow, "begin_flow", return_value=expected_response)
        mocker.patch.object(_OAuthFlow, "continue_flow", return_value=None)

        # setup
        flow = _OAuthFlow(completed_flow_state, mocker.Mock())

        # test
        actual_response = await flow.begin_or_continue_flow(activity)

        # verify
        assert actual_response == expected_response
        _OAuthFlow.begin_flow.assert_called_once()
        _OAuthFlow.continue_flow.assert_not_called()
