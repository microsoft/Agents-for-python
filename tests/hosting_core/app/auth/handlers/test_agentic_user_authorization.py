from math import exp
import pytest

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    RoleTypes,
    TokenResponse
)

from microsoft_agents.authentication.msal import MsalAuth, MsalConnectionManager

from microsoft_agents.hosting.core import (
    AgenticUserAuthorization,
    SignInResponse,
    MemoryStorage,
    FlowStateTag,
)

from tests._common.data import (
    # TEST_FLOW_DATA,
    # TEST_AUTH_DATA,
    # TEST_STORAGE_DATA,
    TEST_DEFAULTS,
    # TEST_ENV_DICT,
    TEST_AGENTIC_ENV_DICT,
    # create_test_auth_handler,
)

from tests._common.testing_objects import (
    # TestingConnectionManager,
    # TestingTokenProvider,
    # agentic_mock_class_MsalAuth,
    TestingConnectionManager as MockConnectionManager,
)

from tests._common.mock_utils import mock_class, mock_instance

from .._common import (
    testing_TurnContext_magic,
)

DEFAULTS = TEST_DEFAULTS()
AGENTIC_ENV_DICT = TEST_AGENTIC_ENV_DICT()


class TestUtils:
    def setup_method(self, mocker):
        self.TurnContext = testing_TurnContext_magic

    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def connection_manager(self, mocker):
        return MsalConnectionManager(**AGENTIC_ENV_DICT)

    @pytest.fixture
    def auth_handler_settings(self):
        return AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][DEFAULTS.agentic_auth_handler_id]["SETTINGS"]

    @pytest.fixture
    def agentic_auth(self, storage, connection_manager, auth_handler_settings):
        return AgenticUserAuthorization(storage, connection_manager,
            auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id)

    @pytest.fixture(params=[RoleTypes.user, RoleTypes.skill, RoleTypes.agent])
    def non_agentic_role(self, request):
        return request.param

    @pytest.fixture(params=[RoleTypes.agentic_user, RoleTypes.agentic_identity])
    def agentic_role(self, request):
        return request.param
    
    def mock_provider(self, mocker, app_token="bot_token", instance_token=None, user_token=None):
        mock_provider = mocker.Mock(spec=MsalAuth)
        mock_provider.get_agentic_instance_token = mocker.AsyncMock(
            return_value=[instance_token, app_token]
        )
        mock_provider.get_agentic_user_token = mocker.AsyncMock(
            return_value=user_token
        )
        return mock_provider

    def mock_class_provider(self, mocker, app_token="bot_token", instance_token=None, user_token=None):
        instance = self.mock_provider(mocker, app_token, instance_token, user_token)
        mock_class(mocker, MsalAuth, instance)


class TestAgenticUserAuthorization(TestUtils):

    def test_get_agent_instance_id_is_agentic(self, mocker, agentic_role):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert (
            AgenticUserAuthorization.get_agent_instance_id(context)
            == DEFAULTS.agentic_instance_id
        )

    def test_get_agent_instance_id_not_agentic(self, mocker, non_agentic_role):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=non_agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticUserAuthorization.get_agent_instance_id(context) is None

    def test_get_agentic_user_is_agentic(self, mocker, agentic_role):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert (
            AgenticUserAuthorization.get_agentic_user(context) == DEFAULTS.agentic_user_id
        )

    def test_get_agentic_user_not_agentic(self, mocker, non_agentic_role):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=non_agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticUserAuthorization.get_agentic_user(context) is None

    @pytest.mark.asyncio
    async def test_get_agentic_instance_token_not_agentic(
        self, mocker, non_agentic_role, agentic_auth
    ):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=non_agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_instance_token(context) is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_not_agentic(
        self, mocker, non_agentic_role, agentic_auth
    ):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=non_agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_user_token(context, ["user.Read"]) is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_agentic_no_user_id(
        self, mocker, agentic_role, agentic_auth
    ):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_user_token(context, ["user.Read"]) is None

    @pytest.mark.asyncio
    async def test_get_agentic_instance_token_is_agentic(
        self, mocker, agentic_role, agentic_auth, auth_handler_settings
    ):
        mock_provider = self.mock_provider(mocker, instance_token=DEFAULTS.token)
        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )

        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)

        token = await agentic_auth.get_agentic_instance_token(context)
        assert token == DEFAULTS.token
        mock_provider.get_agentic_instance_token.assert_called_once_with(DEFAULTS.agentic_instance_id)

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_is_agentic(
        self, mocker, agentic_role, agentic_auth, auth_handler_settings
    ):
        mock_provider = self.mock_provider(mocker, user_token=DEFAULTS.token)

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )

        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)

        token = await agentic_auth.get_agentic_user_token(context, ["user.Read"])
        assert token == DEFAULTS.token
        mock_provider.get_agentic_user_token.assert_called_once_with(
            DEFAULTS.agentic_instance_id, "some_id", ["user.Read"]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scopes_list, expected_scopes_list",
        [
            (["user.Read"], ["user.Read"]),
            ([], ["user.Read", "Mail.Read"]),
            (None, ["user.Read", "Mail.Read"]),
        ],
    )
    async def test_sign_in_success(self, mocker, scopes_list, agentic_role, expected_scopes_list, auth_handler_settings):
        mock_provider = self.mock_provider(mocker, user_token="my_token")

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        res = await agentic_auth.sign_in(context, "my_connection", scopes_list)
        assert res.token_response.token == "my_token"
        assert res.tag == FlowStateTag.COMPLETE

        mock_provider.get_agentic_user_token.assert_called_once_with(
            DEFAULTS.agentic_instance_id, "some_id", expected_scopes_list
        )
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scopes_list, expected_scopes_list",
        [
            (["user.Read"], ["user.Read"]),
            ([], ["user.Read", "Mail.Read"]),
            (None, ["user.Read", "Mail.Read"]),
        ],
    )
    async def test_sign_in_failure(self, mocker, scopes_list, agentic_role, expected_scopes_list, auth_handler_settings):
        mock_provider = self.mock_provider(mocker, user_token=None)

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        res = await agentic_auth.sign_in(context, "my_connection", scopes_list)
        assert not res.token_response
        assert res.tag == FlowStateTag.FAILURE

        mock_provider.get_agentic_user_token.assert_called_once_with(
            DEFAULTS.agentic_instance_id, "some_id", expected_scopes_list
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scopes_list, expected_scopes_list",
        [
            (["user.Read"], ["user.Read"]),
            ([], ["user.Read", "Mail.Read"]),
            (None, ["user.Read", "Mail.Read"]),
        ],
    )
    async def test_get_refreshed_token_success(self, mocker, scopes_list, agentic_role, expected_scopes_list, auth_handler_settings):
        mock_provider = self.mock_provider(mocker, user_token="my_token")

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        res = await agentic_auth.get_refreshed_token(context, "my_connection", scopes_list)
        assert res.token == "my_token"

        mock_provider.get_agentic_user_token.assert_called_once_with(
            DEFAULTS.agentic_instance_id, "some_id", expected_scopes_list
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scopes_list, expected_scopes_list",
        [
            (["user.Read"], ["user.Read"]),
            ([], ["user.Read", "Mail.Read"]),
            (None, ["user.Read", "Mail.Read"]),
        ],
    )
    async def test_get_refreshed_token_failure(self, mocker, scopes_list, agentic_role, expected_scopes_list, auth_handler_settings):
        mock_provider = self.mock_provider(mocker, user_token=None)

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticUserAuthorization(
            MemoryStorage(), connection_manager, auth_handler_settings=auth_handler_settings, auth_handler_id=DEFAULTS.agentic_auth_handler_id
        )
        activity = Activity(
            type="message",
            recipient=ChannelAccount(
                id="some_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=agentic_role,
            ),
        )
        context = self.TurnContext(mocker, activity=activity)
        res = await agentic_auth.get_refreshed_token(context, "my_connection", scopes_list)
        assert not res
        mock_provider.get_agentic_user_token.assert_called_once_with(
            DEFAULTS.agentic_instance_id, "some_id", expected_scopes_list
        )