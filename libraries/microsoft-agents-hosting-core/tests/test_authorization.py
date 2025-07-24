import pytest
from .tools.testing_authorization import (
    TestingAuthorization,
    create_test_auth_handler,
)
from .tools.testing_utility import TestingUtility
import jwt
from unittest.mock import Mock, AsyncMock
from microsoft.agents.hosting.core import SignInState
from microsoft.agents.hosting.core.oauth_flow import FlowState


class TestAuthorization:
    def setup_method(self):
        self.turn_context = TestingUtility.create_empty_context()

    @pytest.mark.asyncio
    async def test_authorization_get_token_single_handler(self):
        """
        Test Authorization - get_token() with single Auth Handler
        """
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth-a"),
            }
        )

        token_res = await auth.get_token(self.turn_context)
        auth_handler = auth.resolver_handler("auth-handler")
        assert token_res.connection_name == auth_handler.abs_oauth_connection_name
        assert token_res.token == f"{auth_handler.abs_oauth_connection_name}-token"

    @pytest.mark.asyncio
    async def test_authorization_get_token_multiple_handlers(self):
        """
        Test Authorization - get_token() with multiple Auth Handlers
        """
        auth_handlers = {
            "auth-handler": create_test_auth_handler("test-auth-a"),
            "auth-handler-obo": create_test_auth_handler("test-auth-b", obo=True),
            "auth-handler-with-title": create_test_auth_handler(
                "test-auth-c", title="test-title"
            ),
            "auth-handler-with-title-text": create_test_auth_handler(
                "test-auth-d", title="test-title", text="test-text"
            ),
        }
        auth = TestingAuthorization(auth_handlers=auth_handlers)
        for id, auth_handler in auth_handlers.items():
            # test value propogation
            token_res = await auth.get_token(self.turn_context, id)
            assert token_res.connection_name == auth_handler.abs_oauth_connection_name
            assert token_res.token == f"{auth_handler.abs_oauth_connection_name}-token"

    @pytest.mark.asyncio
    async def test_authorization_exchange_token_valid_token(self):
        valid_token = jwt.encode({"aud": "api://botframework.test.api"}, "")
        scopes = ["scope-a"]
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth", obo=True),
            },
            token=valid_token,
        )
        token_res = await auth.exchange_token(self.turn_context, scopes=scopes)
        assert (
            token_res.token
            == f"{auth.resolver_handler().obo_connection_name}-obo-token"
        )

    @pytest.mark.asyncio
    async def test_authorization_exchange_token_invalid_token(self):
        invalid_token = jwt.encode({"aud": "invalid://botframework.test.api"}, "")
        scopes = ["scope-a"]
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth"),
            },
            token=invalid_token,
        )
        token_res = await auth.exchange_token(self.turn_context, scopes=scopes)
        assert token_res.token == invalid_token

    @pytest.mark.asyncio
    async def test_authorization_get_flow_state_unavailable(self):
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth-a"),
            }
        )

        assert auth.get_flow_state() == FlowState()

    @pytest.mark.asyncio
    async def test_authorization_begin_or_continue_flow_not_started(self):
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth-a"),
            },
            token=None,
        )
        mock_turn_state = AsyncMock(get_value=Mock(return_value=SignInState()))

        token_res = await auth.begin_or_continue_flow(
            self.turn_context,
            mock_turn_state,
            "auth-handler",
        )
        # Test value propogation
        auth_handler = auth.resolver_handler("auth-handler")
        assert token_res.connection_name == auth_handler.abs_oauth_connection_name
        assert token_res.token == f"{auth_handler.abs_oauth_connection_name}-token"

        # Test function calls
        auth_handler.flow._get_flow_state.assert_called_once()
        auth_handler.flow.begin_flow.assert_called_once()
        mock_turn_state.save.assert_called_once_with(self.turn_context)
        mock_turn_state.set_value.assert_called_once_with(
            auth.SIGN_IN_STATE_KEY,
            SignInState(
                continuation_activity=self.turn_context.activity,
                handler_id="auth-handler",
            ),
        )

    @pytest.mark.asyncio
    async def test_authorization_begin_or_continue_flow_started(self):
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth-a"),
            },
            token=None,
            flow_started=True,
        )
        mock_turn_state = AsyncMock(get_value=Mock(return_value=SignInState()))
        token_res = await auth.begin_or_continue_flow(
            self.turn_context,
            mock_turn_state,
            "auth-handler",
        )

        # Test value propogation
        auth_handler = auth.resolver_handler("auth-handler")
        assert token_res.connection_name == auth_handler.abs_oauth_connection_name
        assert token_res.token == f"{auth_handler.abs_oauth_connection_name}-token"

        # Test function calls
        auth_handler.flow._get_flow_state.assert_called_once()
        auth_handler.flow.continue_flow.assert_called_once()
        mock_turn_state.save.assert_called_once_with(self.turn_context)
        mock_turn_state.delete_value.assert_called_once_with(auth.SIGN_IN_STATE_KEY)

    @pytest.mark.asyncio
    async def test_authorization_begin_or_continue_flow_started_with_handler(self):
        auth = TestingAuthorization(
            auth_handlers={
                "auth-handler": create_test_auth_handler("test-auth-a"),
            },
            token=None,
            flow_started=True,
        )
        mock_turn_state = AsyncMock(get_value=Mock(return_value=SignInState()))
        auth.on_sign_in_success(AsyncMock())

        token_res = await auth.begin_or_continue_flow(
            self.turn_context,
            mock_turn_state,
            "auth-handler",
        )

        # Test value propogation
        auth_handler = auth.resolver_handler("auth-handler")
        assert token_res.connection_name == auth_handler.abs_oauth_connection_name
        assert token_res.token == f"{auth_handler.abs_oauth_connection_name}-token"

        # Test function calls
        auth_handler.flow._get_flow_state.assert_called_once()
        auth_handler.flow.continue_flow.assert_called_once()
        mock_turn_state.save.assert_called_once_with(self.turn_context)
        mock_turn_state.delete_value.assert_called_once_with(auth.SIGN_IN_STATE_KEY)
        auth._sign_in_handler.assert_called_once_with(
            self.turn_context, mock_turn_state, "auth-handler"
        )
