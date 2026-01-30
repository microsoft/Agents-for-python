import pytest
import jwt

from microsoft_agents.activity import ActivityTypes, TokenResponse

from microsoft_agents.authentication.msal import MsalAuth, MsalConnectionManager

from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app.oauth import _UserAuthorization, _SignInResponse
from microsoft_agents.hosting.core._oauth import (
    _FlowStorageClient,
    _FlowStateTag,
    _FlowState,
    _FlowResponse,
    _OAuthFlow,
)

# test constants
from tests._common.data import (
    FLOW_TEST_DATA,
    AUTH_TEST_DATA,
    STORAGE_TEST_DATA,
    DEFAULT_TEST_VALUES,
    AGENTIC_TEST_ENV_DICT,
)
from tests._common.data.storage_test_data import STORAGE_TEST_DATA
from tests._common.mock_utils import mock_instance
from tests._common.fixtures import FlowStateFixtures
from tests._common.testing_objects import (
    mock_class_OAuthFlow,
    mock_UserTokenClient,
)
from tests.hosting_core._common import flow_state_eq

DEFAULTS = DEFAULT_TEST_VALUES()
FLOW_DATA = FLOW_TEST_DATA()
STORAGE_DATA = STORAGE_TEST_DATA()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


def make_jwt(token: str = DEFAULTS.token, aud="1234567", app_id="1234567"):
    if aud:
        return jwt.encode({"aud": aud, "appid": app_id}, token, algorithm="HS256")
    else:
        return jwt.encode({}, token, algorithm="HS256")


class MyUserAuthorization(_UserAuthorization):
    async def _handle_flow_response(self, *args, **kwargs):
        pass


def create_testing_TurnContext(
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


async def read_state(
    storage,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    auth_handler_id=DEFAULTS.auth_handler_id,
):
    storage_client = _FlowStorageClient(channel_id, user_id, storage)
    key = storage_client.key(auth_handler_id)
    return (await storage.read([key], target_cls=_FlowState)).get(key)


def mock_provider(mocker, exchange_token=None):
    instance = mock_instance(
        mocker, MsalAuth, {"acquire_token_on_behalf_of": exchange_token}
    )
    mocker.patch.object(MsalConnectionManager, "get_connection", return_value=instance)
    return instance


class TestEnv(FlowStateFixtures):
    def setup_method(self):
        self.TurnContext = create_testing_TurnContext

    @pytest.fixture
    def context(self, mocker):
        return self.TurnContext(mocker)

    @pytest.fixture
    def storage(self):
        return MemoryStorage(STORAGE_DATA.get_init_data())

    @pytest.fixture
    def connection_manager(self):
        return MsalConnectionManager(**AGENTIC_ENV_DICT)

    @pytest.fixture
    def auth_handlers(self):
        return AUTH_TEST_DATA().auth_handlers

    @pytest.fixture
    def auth_handler_settings(self):
        return AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][
            DEFAULTS.auth_handler_id
        ]["SETTINGS"]

    @pytest.fixture
    def user_authorization(self, connection_manager, storage, auth_handler_settings):
        return MyUserAuthorization(
            storage,
            connection_manager,
            auth_handler_settings=auth_handler_settings,
            auth_handler_id=DEFAULTS.auth_handler_id,
        )

    @pytest.fixture
    def exchangeable_token(self):
        jwt.encode({"aud": "exchange_audience"}, "secret", algorithm="HS256")

    @pytest.fixture(
        params=[
            [None, ["scope1", "scope2"]],
            [[], ["scope1", "scope2"]],
            [["scope1"], ["scope1"]],
        ]
    )
    def scope_set(self, request):
        return request.param

    @pytest.fixture(
        params=[
            ["AGENTIC", "AGENTIC"],
            [None, DEFAULTS.obo_connection_name],
            ["", DEFAULTS.obo_connection_name],
        ]
    )
    def connection_set(self, request):
        return request.param


class TestUserAuthorization(TestEnv):

    # TODO -> test init

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "flow_response, exchange_attempted, token_exchange_response, expected_response",
        [
            [
                _FlowResponse(
                    token_response=TokenResponse(token=make_jwt()),
                    flow_state=_FlowState(
                        tag=_FlowStateTag.COMPLETE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                True,
                "wow",
                _SignInResponse(
                    token_response=TokenResponse(token="wow"),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                _FlowResponse(
                    token_response=TokenResponse(token=make_jwt(aud=None)),
                    flow_state=_FlowState(
                        tag=_FlowStateTag.COMPLETE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                False,
                "wow",
                _SignInResponse(
                    token_response=TokenResponse(token=make_jwt(aud=None)),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                _FlowResponse(
                    token_response=TokenResponse(
                        token=make_jwt(token="some_value", aud="other")
                    ),
                    flow_state=_FlowState(
                        tag=_FlowStateTag.COMPLETE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                False,
                DEFAULTS.token,
                _SignInResponse(
                    token_response=TokenResponse(
                        token=make_jwt("some_value", aud="other")
                    ),
                    tag=_FlowStateTag.COMPLETE,
                ),
            ],
            [
                _FlowResponse(
                    token_response=TokenResponse(token=make_jwt(token="some_value")),
                    flow_state=_FlowState(
                        tag=_FlowStateTag.COMPLETE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                True,
                None,
                _SignInResponse(tag=_FlowStateTag.FAILURE),
            ],
            [
                _FlowResponse(
                    flow_state=_FlowState(
                        tag=_FlowStateTag.BEGIN,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                False,
                None,
                _SignInResponse(tag=_FlowStateTag.BEGIN),
            ],
            [
                _FlowResponse(
                    flow_state=_FlowState(
                        tag=_FlowStateTag.CONTINUE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                False,
                None,
                _SignInResponse(tag=_FlowStateTag.CONTINUE),
            ],
            [
                _FlowResponse(
                    flow_state=_FlowState(
                        tag=_FlowStateTag.FAILURE,
                        auth_handler_id=DEFAULTS.auth_handler_id,
                    ),
                ),
                False,
                None,
                _SignInResponse(tag=_FlowStateTag.FAILURE),
            ],
        ],
    )
    async def test_sign_in(
        self,
        mocker,
        user_authorization,
        context,
        storage,
        flow_response,
        exchange_attempted,
        token_exchange_response,
        expected_response,
        scope_set,
        connection_set,
    ):
        request_scopes, expected_scopes = scope_set
        request_connection, expected_connection = connection_set
        mock_class_OAuthFlow(mocker, begin_or_continue_flow_return=flow_response)
        provider = mock_provider(mocker, exchange_token=token_exchange_response)

        sign_in_response = await user_authorization._sign_in(
            context, request_connection, request_scopes
        )
        assert sign_in_response.token_response == expected_response.token_response
        assert sign_in_response.tag == expected_response.tag

        state = await read_state(storage, auth_handler_id=DEFAULTS.auth_handler_id)
        assert flow_state_eq(state, flow_response.flow_state)
        if exchange_attempted:
            MsalConnectionManager.get_connection.assert_called_once_with(
                expected_connection
            )
            provider.acquire_token_on_behalf_of.assert_called_once_with(
                scopes=expected_scopes,
                user_assertion=flow_response.token_response.token,
            )

    @pytest.mark.asyncio
    async def test_sign_out_individual(
        self, mocker, storage, user_authorization, context
    ):
        mock_class_OAuthFlow(mocker)
        await user_authorization._sign_out(context)
        assert (
            await read_state(storage, auth_handler_id=DEFAULTS.auth_handler_id) is None
        )
        _OAuthFlow.sign_out.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "get_user_token_return, exchange_attempted, token_exchange_response, expected_response",
        [
            [TokenResponse(token=make_jwt()), True, "wow", TokenResponse(token="wow")],
            [
                TokenResponse(token=make_jwt(aud=None)),
                False,
                "wow",
                TokenResponse(token=make_jwt(aud=None)),
            ],
            [
                TokenResponse(token=make_jwt(token="some_value", aud="other")),
                False,
                DEFAULTS.token,
                TokenResponse(token=make_jwt("some_value", aud="other")),
            ],
            [
                TokenResponse(token=make_jwt(token="some_value")),
                True,
                None,
                TokenResponse(),
            ],
            [TokenResponse(), False, None, TokenResponse()],
        ],
    )
    async def test_get_refreshed_token(
        self,
        mocker,
        user_authorization,
        context,
        storage,
        get_user_token_return,
        exchange_attempted,
        token_exchange_response,
        expected_response,
        scope_set,
        connection_set,
    ):
        request_scopes, expected_scopes = scope_set
        request_connection, expected_connection = connection_set
        mock_class_OAuthFlow(mocker, get_user_token_return=get_user_token_return)
        provider = mock_provider(mocker, exchange_token=token_exchange_response)

        state_before = await read_state(
            storage, auth_handler_id=DEFAULTS.auth_handler_id
        )
        token_response = await user_authorization.get_refreshed_token(
            context, request_connection, request_scopes
        )
        assert token_response == expected_response

        state = await read_state(storage, auth_handler_id=DEFAULTS.auth_handler_id)

        if state:
            assert flow_state_eq(state, state_before)
        if exchange_attempted:
            MsalConnectionManager.get_connection.assert_called_once_with(
                expected_connection
            )
            provider.acquire_token_on_behalf_of.assert_called_once_with(
                scopes=expected_scopes, user_assertion=get_user_token_return.token
            )
