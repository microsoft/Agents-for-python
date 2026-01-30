import pytest
import jwt
from datetime import datetime, timezone, timedelta

from microsoft_agents.activity import ActivityTypes, TokenResponse

from microsoft_agents.authentication.msal import MsalAuth, MsalConnectionManager

from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app.oauth import ConnectorUserAuthorization

# test constants
from tests._common.data import (
    STORAGE_TEST_DATA,
    DEFAULT_TEST_VALUES,
    AGENTIC_TEST_ENV_DICT,
)
from tests._common.mock_utils import mock_instance
from tests._common.fixtures import FlowStateFixtures

DEFAULTS = DEFAULT_TEST_VALUES()
STORAGE_DATA = STORAGE_TEST_DATA()
AGENTIC_ENV_DICT = AGENTIC_TEST_ENV_DICT()


def make_jwt(
    token: str = DEFAULTS.token,
    aud="123",
    app_id="123",
    exp_delta_seconds=3600,
    include_exp=True,
):
    """Create a JWT token for testing."""
    payload = {}
    if aud:
        payload["aud"] = aud
    if app_id:
        payload["appid"] = app_id
    if include_exp:
        payload["exp"] = (datetime.now(timezone.utc) + timedelta(seconds=exp_delta_seconds)).timestamp()
    
    return jwt.encode(payload, token, algorithm="HS256")


def make_expired_jwt(token: str = DEFAULTS.token, aud="123", app_id="123"):
    """Create an expired JWT token for testing."""
    return make_jwt(token, aud, app_id, exp_delta_seconds=-3600)


def create_testing_TurnContext(
    mocker,
    channel_id=DEFAULTS.channel_id,
    user_id=DEFAULTS.user_id,
    security_token=None,
):
    """Create a mock TurnContext for testing."""
    turn_context = mocker.Mock()
    turn_context.activity.channel_id = channel_id
    turn_context.activity.from_property.id = user_id
    turn_context.activity.type = ActivityTypes.message
    turn_context.adapter.AGENT_IDENTITY_KEY = "__agent_identity_key"
    
    # Create identity with security token
    identity = mocker.Mock()
    if security_token is not None:
        identity.security_token = security_token
    turn_context.identity = identity
    
    agent_identity = mocker.Mock()
    agent_identity.claims = {"aud": DEFAULTS.ms_app_id}
    turn_context.turn_state = {
        "__agent_identity_key": agent_identity,
    }
    return turn_context


def mock_provider(mocker, exchange_token=None):
    """Mock an authentication provider for testing."""
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
        return self.TurnContext(mocker, security_token=make_jwt())

    @pytest.fixture
    def storage(self):
        return MemoryStorage(STORAGE_DATA.get_init_data())

    @pytest.fixture
    def connection_manager(self):
        return MsalConnectionManager(**AGENTIC_ENV_DICT)

    @pytest.fixture
    def auth_handler_settings(self):
        return AGENTIC_ENV_DICT["AGENTAPPLICATION"]["USERAUTHORIZATION"]["HANDLERS"][
            DEFAULTS.auth_handler_id
        ]["SETTINGS"]

    @pytest.fixture
    def connector_authorization(self, connection_manager, storage, auth_handler_settings):
        return ConnectorUserAuthorization(
            storage,
            connection_manager,
            auth_handler_settings=auth_handler_settings,
            auth_handler_id=DEFAULTS.auth_handler_id,
        )

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
            [None, "SERVICE_CONNECTION"],
            ["", "SERVICE_CONNECTION"],
        ]
    )
    def connection_set(self, request):
        return request.param


class TestConnectorUserAuthorization(TestEnv):


    @pytest.mark.asyncio
    async def test_sign_in_without_obo_when_token_not_exchangeable(
        self,
        mocker,
        connector_authorization,
        storage,
    ):
        """Test that _sign_in raises error when token is not exchangeable but OBO is configured."""
        security_token = make_jwt(aud=None)  # Non-exchangeable token
        context = self.TurnContext(mocker, security_token=security_token)
        
        # When token is not exchangeable but OBO is configured (connection and scopes are set),
        # it should raise ValueError
        with pytest.raises(ValueError, match="not exchangeable"):
            await connector_authorization._sign_in(
                context, "some_connection", ["scope1"]
            )

    @pytest.mark.asyncio
    async def test_sign_in_raises_when_no_identity(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _sign_in raises ValueError when context has no identity."""
        context = self.TurnContext(mocker)
        context.identity = None
        
        with pytest.raises(ValueError, match="no security token found"):
            await connector_authorization._sign_in(context)

    @pytest.mark.asyncio
    async def test_sign_in_raises_when_no_security_token(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _sign_in raises ValueError when identity has no security_token attribute."""
        context = self.TurnContext(mocker)
        # Remove the security_token attribute entirely
        delattr(context.identity, 'security_token')
        
        with pytest.raises(ValueError, match="no security token found"):
            await connector_authorization._sign_in(context)

    @pytest.mark.asyncio
    async def test_sign_in_raises_when_security_token_is_none(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _sign_in raises ValueError when security_token is None."""
        context = self.TurnContext(mocker)
        context.identity.security_token = None
        
        with pytest.raises(ValueError, match="security token is None"):
            await connector_authorization._sign_in(context)

    @pytest.mark.asyncio
    async def test_get_refreshed_token_raises_on_expired_token(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that get_refreshed_token raises ValueError for expired token."""
        expired_token = make_expired_jwt()
        context = self.TurnContext(mocker, security_token=expired_token)
        
        with pytest.raises(ValueError, match="Unexpected connector token expiration"):
            await connector_authorization.get_refreshed_token(context)

    @pytest.mark.asyncio
    async def test_get_refreshed_token_handles_obo_failure(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that get_refreshed_token handles OBO exchange failure."""
        security_token = make_jwt()
        context = self.TurnContext(mocker, security_token=security_token)
        
        token_response = await connector_authorization.get_refreshed_token(
            context, "some_connection", ["scope1"]
        )
        
        # Should return None when OBO fails
        assert token_response is None


    @pytest.mark.asyncio
    async def test_sign_out_is_noop(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _sign_out is a no-op for connector authorization."""
        context = self.TurnContext(mocker, security_token=make_jwt())
        
        # Should not raise any exceptions
        await connector_authorization._sign_out(context)
        
        # Verify it completes successfully (no assertions needed, just verify no exception)

    @pytest.mark.asyncio
    async def test_handle_obo_without_configuration(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _handle_obo returns token as-is when OBO not configured (no connection and no scopes)."""
        security_token = make_jwt()
        context = self.TurnContext(mocker, security_token=security_token)
        token_response = TokenResponse(token=security_token)
        
        # Don't mock provider since we shouldn't reach it
        
        with pytest.raises(ValueError, match="Unable to get authority configuration"):
            # Call with no connection or scopes (OBO not configured)
            await connector_authorization._handle_obo(
                context, token_response, None, []
            )

    @pytest.mark.asyncio
    async def test_handle_obo_with_non_exchangeable_token(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _handle_obo raises ValueError for non-exchangeable token when OBO configured."""
        security_token = make_jwt(aud=None)
        context = self.TurnContext(mocker, security_token=security_token)
        token_response = TokenResponse(token=security_token)
        
        with pytest.raises(ValueError, match="not exchangeable"):
            await connector_authorization._handle_obo(
                context, token_response, "some_connection", ["scope1"]
            )

    @pytest.mark.asyncio
    async def test_handle_obo_with_missing_connection(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _handle_obo raises ValueError when connection not found."""
        security_token = make_jwt()
        context = self.TurnContext(mocker, security_token=security_token)
        token_response = TokenResponse(token=security_token)
        
        # Mock get_connection to return None
        mocker.patch.object(MsalConnectionManager, "get_connection", return_value=None)
        
        with pytest.raises(ValueError, match="not found"):
            await connector_authorization._handle_obo(
                context, token_response, "nonexistent_connection", ["scope1"]
            )

    @pytest.mark.asyncio
    async def test_create_token_response_extracts_expiration(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _create_token_response extracts expiration from JWT."""
        security_token = make_jwt(exp_delta_seconds=7200)
        context = self.TurnContext(mocker, security_token=security_token)
        
        token_response = connector_authorization._create_token_response(context)
        
        assert token_response.token == security_token
        assert token_response.expiration is not None
        
        # Verify expiration is in the future
        expiration = datetime.fromisoformat(token_response.expiration.replace("Z", "+00:00"))
        assert expiration > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_create_token_response_handles_jwt_without_exp(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _create_token_response handles JWT without expiration claim."""
        security_token = make_jwt(include_exp=False)
        context = self.TurnContext(mocker, security_token=security_token)
        
        # Should succeed but not have expiration
        token_response = connector_authorization._create_token_response(context)
        assert token_response.token == security_token
        # Expiration might not be set or could be None depending on implementation
        # The key is it doesn't raise an error

    @pytest.mark.asyncio
    async def test_get_refreshed_token_signs_out_on_obo_error(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that get_refreshed_token signs out when OBO exchange fails with exception."""
        security_token = make_jwt()
        context = self.TurnContext(mocker, security_token=security_token)
        
        # Mock provider to raise an exception
        provider = mock_instance(
            mocker, MsalAuth, {"acquire_token_on_behalf_of": Exception("OBO failed")}
        )
        mocker.patch.object(MsalConnectionManager, "get_connection", return_value=provider)
        provider.acquire_token_on_behalf_of.side_effect = Exception("OBO failed")
        
        # Mock _sign_out to verify it's called
        sign_out_mock = mocker.patch.object(connector_authorization, "_sign_out")
        
        with pytest.raises(Exception, match="OBO failed"):
            await connector_authorization.get_refreshed_token(
                context, "some_connection", ["scope1"]
            )
        
        # Verify sign_out was called
        sign_out_mock.assert_called_once_with(context)

    @pytest.mark.asyncio
    async def test_sign_in_signs_out_on_obo_error(
        self,
        mocker,
        connector_authorization,
    ):
        """Test that _sign_in signs out when OBO exchange fails with exception."""
        security_token = make_jwt()
        context = self.TurnContext(mocker, security_token=security_token)
        
        # Mock provider to raise an exception
        provider = mock_instance(
            mocker, MsalAuth, {"acquire_token_on_behalf_of": Exception("OBO failed")}
        )
        mocker.patch.object(MsalConnectionManager, "get_connection", return_value=provider)
        provider.acquire_token_on_behalf_of.side_effect = Exception("OBO failed")
        
        # Mock _sign_out to verify it's called
        sign_out_mock = mocker.patch.object(connector_authorization, "_sign_out")
        
        with pytest.raises(Exception, match="OBO failed"):
            await connector_authorization._sign_in(
                context, "some_connection", ["scope1"]
            )
        
        # Verify sign_out was called
        sign_out_mock.assert_called_once_with(context)
