import pytest
from microsoft.agents.hosting.core import Authorization, MemoryStorage
from .tools.testing_authorization import (
    TestingAuthorization,
    create_test_auth_handler,
    MockOAuthFlow,
)
from .tools.testing_utility import TestingUtility
from unittest.mock import Mock
import jwt


class TestAuthorization:

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

        token_res = await auth.get_token(TestingUtility.create_empty_context())
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
            token_res = await auth.get_token(TestingUtility.create_empty_context(), id)
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
        token_res = await auth.exchange_token(
            TestingUtility.create_empty_context(), scopes=scopes
        )
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
        token_res = await auth.exchange_token(
            TestingUtility.create_empty_context(), scopes=scopes
        )
        assert token_res.token == invalid_token
