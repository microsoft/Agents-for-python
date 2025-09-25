import pytest

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    RoleTypes
)

from microsoft_agents.authentication.msal import MsalAuth, MsalConnectionManager

from microsoft_agents.hosting.core import (
    AgenticAuthorization,
    SignInResponse,
    MemoryStorage
)

from tests._common.data import (
    TEST_FLOW_DATA,
    TEST_AUTH_DATA,
    TEST_STORAGE_DATA,
    TEST_DEFAULTS,
    TEST_ENV_DICT,
    TEST_AGENTIC_ENV_DICT,
    create_test_auth_handler,
)

from tests._common.testing_objects import (
    TestingConnectionManager,
    TestingTokenProvider,
    agentic_mock_class_MsalAuth,
    TestingConnectionManager as MockConnectionManager,
)

from ._common import (
    testing_TurnContext_magic,
)

DEFAULTS = TEST_DEFAULTS()
AGENTIC_ENV_DICT = TEST_AGENTIC_ENV_DICT()

class TestUtils:

    def setup_method(self):
        self.TurnContext = testing_TurnContext_magic

    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def connection_manager(self, mocker):
        return MockConnectionManager()

    @pytest.fixture
    def agentic_auth(self, mocker, storage, connection_manager):
        return AgenticAuthorization(
            storage,
            connection_manager,
            **AGENTIC_ENV_DICT
        )

    @pytest.fixture(params=[RoleTypes.user, RoleTypes.skill, RoleTypes.agent])
    def non_agentic_role(self, request):
        return request.param

    @pytest.fixture(params=[RoleTypes.agentic_user, RoleTypes.agentic_identity])
    def agentic_role(self, request):
        return request.param

class TestAgenticAuthorization(TestUtils):

    @pytest.mark.parametrize("activity", [
        Activity(
            type="message",
            recipient=ChannelAccount(
                id="bot_id",
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=RoleTypes.agent,
            )
        ),
        Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
                agentic_app_id=DEFAULTS.agentic_instance_id,
                role=RoleTypes.agentic_user,
            )
        ),
        Activity(
            type="message",
            recipient=ChannelAccount(
                id=DEFAULTS.agentic_user_id,
            )
        ),
        Activity(
            type="message",
            recipient=ChannelAccount(id="some_id")
        )
    ])
    def test_is_agentic_request(self, mocker, activity):
        assert activity.is_agentic() == AgenticAuthorization.is_agentic_request(activity)
        context = self.TurnContext(mocker, activity=activity)
        assert activity.is_agentic() == AgenticAuthorization.is_agentic_request(context)

    def test_get_agent_instance_id_is_agentic(self, mocker, agentic_role):
        activity = Activity(type="message", recipient=ChannelAccount(id="some_id", agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticAuthorization.get_agent_instance_id(context) == DEFAULTS.agentic_instance_id

    def test_get_agent_instance_id_not_agentic(self, mocker, non_agentic_role):
        activity = Activity(type="message", recipient=ChannelAccount(id="some_id", agentic_app_id=DEFAULTS.agentic_instance_id, role=non_agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticAuthorization.get_agent_instance_id(context) is None

    def test_get_agentic_user_is_agentic(self, mocker, agentic_role):
        activity = Activity(type="message", recipient=ChannelAccount(id=DEFAULTS.agentic_user_id, agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticAuthorization.get_agentic_user(context) == DEFAULTS.agentic_user_id

    def test_get_agentic_user_not_agentic(self, mocker, non_agentic_role):
        activity = Activity(type="message", recipient=ChannelAccount(id=DEFAULTS.agentic_user_id, agentic_app_id=DEFAULTS.agentic_instance_id, role=non_agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert AgenticAuthorization.get_agentic_user(context) is None

    @pytest.mark.asyncio
    async def test_get_agentic_instance_token_not_agentic(self, mocker, non_agentic_role, agentic_auth):
        activity = Activity(type="message", recipient=ChannelAccount(id=DEFAULTS.agentic_user_id, agentic_app_id=DEFAULTS.agentic_instance_id, role=non_agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_instance_token(context) is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_not_agentic(self, mocker, non_agentic_role, agentic_auth):
        activity = Activity(type="message", recipient=ChannelAccount(id=DEFAULTS.agentic_user_id, agentic_app_id=DEFAULTS.agentic_instance_id, role=non_agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_user_token(context, ["user.Read"]) is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_agentic_no_user_id(self, mocker, agentic_role, agentic_auth):
        activity = Activity(type="message", recipient=ChannelAccount(agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role))
        context = self.TurnContext(mocker, activity=activity)
        assert await agentic_auth.get_agentic_user_token(context, ["user.Read"]) is None

    @pytest.mark.asyncio
    async def test_get_agentic_instance_token_is_agentic(self, mocker, agentic_role, agentic_auth):
        mock_provider = mocker.Mock(spec=MsalAuth)
        mock_provider.get_agentic_instance_token = mocker.AsyncMock(return_value=[DEFAULTS.token, "bot_id"])

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticAuthorization(
            MemoryStorage(),
            connection_manager,
            **AGENTIC_ENV_DICT
        )

        activity = Activity(type="message", recipient=ChannelAccount(id="some_id", agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role))
        context = self.TurnContext(mocker, activity=activity)

        token = await agentic_auth.get_agentic_instance_token(context)
        assert token == DEFAULTS.token

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_is_agentic(self, mocker, agentic_role, agentic_auth):
        mock_provider = mocker.Mock(spec=MsalAuth)
        mock_provider.get_agentic_user_token = mocker.AsyncMock(return_value=DEFAULTS.token)

        connection_manager = mocker.Mock(spec=MsalConnectionManager)
        connection_manager.get_token_provider = mocker.Mock(return_value=mock_provider)

        agentic_auth = AgenticAuthorization(
            MemoryStorage(),
            connection_manager,
            **AGENTIC_ENV_DICT
        )

        activity = Activity(type="message", recipient=ChannelAccount(id="some_id", agentic_app_id=DEFAULTS.agentic_instance_id, role=agentic_role))
        context = self.TurnContext(mocker, activity=activity)

        token = await agentic_auth.get_agentic_user_token(context, ["user.Read"])
        assert token == DEFAULTS.token

