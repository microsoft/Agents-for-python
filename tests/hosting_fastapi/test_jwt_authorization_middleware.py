# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization import (
    ClaimsIdentity,
    JwtTokenValidator,
)
from microsoft_agents.hosting.fastapi import JwtAuthorizationMiddleware


@pytest.fixture
def app_with_middleware():
    """Create a FastAPI app with JWT middleware for testing"""
    from fastapi import Request

    app = FastAPI()
    app.add_middleware(JwtAuthorizationMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        claims_identity = getattr(request.state, "claims_identity", None)
        return {
            "authenticated": (
                claims_identity.is_authenticated if claims_identity else False
            ),
            "claims": claims_identity.claims if claims_identity else {},
        }

    return app


@pytest.fixture
def auth_config_anonymous():
    """Create auth config that allows anonymous access"""
    return AgentAuthConfiguration(
        client_id=None, tenant_id=None  # No client_id means anonymous is allowed
    )


@pytest.fixture
def auth_config_with_client_id():
    """Create auth config with client_id (requires authentication)"""
    return AgentAuthConfiguration(
        client_id="test-client-id", tenant_id="test-tenant-id"
    )


class TestJwtAuthorizationMiddleware:
    """Tests for JWT Authorization Middleware"""

    def test_anonymous_claims_without_await(
        self, app_with_middleware, auth_config_anonymous
    ):
        """
        Test that get_anonymous_claims() is called without await when no auth header is present
        and anonymous access is allowed (no CLIENT_ID configured).

        This is the primary test for the bug fix - ensuring that get_anonymous_claims()
        is not awaited since it's a synchronous method.
        """
        # Set up the app state with anonymous auth config
        app_with_middleware.state.agent_configuration = auth_config_anonymous

        # Mock the JwtTokenValidator.get_anonymous_claims to verify it's called correctly
        with patch.object(
            JwtTokenValidator, "get_anonymous_claims"
        ) as mock_get_anonymous:
            mock_claims = ClaimsIdentity({}, False, authentication_type="Anonymous")
            mock_get_anonymous.return_value = mock_claims

            # Make request without Authorization header
            client = TestClient(app_with_middleware)
            response = client.get("/test")

            # Verify the response
            assert response.status_code == 200
            assert response.json()["authenticated"] is False
            assert response.json()["claims"] == {}

            # Verify get_anonymous_claims was called
            mock_get_anonymous.assert_called_once()

    def test_missing_auth_header_with_client_id_returns_401(
        self, app_with_middleware, auth_config_with_client_id
    ):
        """
        Test that missing Authorization header returns 401 when CLIENT_ID is configured
        """
        app_with_middleware.state.agent_configuration = auth_config_with_client_id

        client = TestClient(app_with_middleware)
        response = client.get("/test")

        assert response.status_code == 401
        assert "Authorization header not found" in response.json()["error"]

    def test_invalid_auth_header_format_returns_401(
        self, app_with_middleware, auth_config_with_client_id
    ):
        """
        Test that invalid Authorization header format returns 401
        """
        app_with_middleware.state.agent_configuration = auth_config_with_client_id

        client = TestClient(app_with_middleware)
        response = client.get("/test", headers={"Authorization": "InvalidFormat"})

        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["error"]

    def test_valid_token_sets_claims_identity(
        self, app_with_middleware, auth_config_with_client_id
    ):
        """
        Test that a valid JWT token is validated and claims are set
        """
        app_with_middleware.state.agent_configuration = auth_config_with_client_id

        # Mock the validate_token method
        with patch.object(
            JwtTokenValidator, "validate_token", new_callable=AsyncMock
        ) as mock_validate:
            mock_claims = ClaimsIdentity(
                {"aud": "test-client-id", "sub": "test-user"},
                True,
                security_token="test-token",
            )
            mock_validate.return_value = mock_claims

            client = TestClient(app_with_middleware)
            response = client.get(
                "/test", headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            assert response.json()["authenticated"] is True
            assert response.json()["claims"]["aud"] == "test-client-id"

            # Verify validate_token was called with the correct token
            mock_validate.assert_called_once_with("test-token")

    def test_invalid_token_returns_401(
        self, app_with_middleware, auth_config_with_client_id
    ):
        """
        Test that an invalid JWT token returns 401
        """
        app_with_middleware.state.agent_configuration = auth_config_with_client_id

        # Mock the validate_token method to raise ValueError
        with patch.object(
            JwtTokenValidator, "validate_token", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.side_effect = ValueError("Invalid token")

            client = TestClient(app_with_middleware)
            response = client.get(
                "/test", headers={"Authorization": "Bearer invalid-token"}
            )

            assert response.status_code == 401
            assert "Invalid token or authentication failed" in response.json()["error"]

    def test_anonymous_access_with_no_auth_config(self, app_with_middleware):
        """
        Test that anonymous access is allowed when auth_config is None
        """
        # Don't set agent_configuration on the app state (simulating no config)
        # This will result in auth_config being None

        with patch.object(
            JwtTokenValidator, "get_anonymous_claims"
        ) as mock_get_anonymous:
            mock_claims = ClaimsIdentity({}, False, authentication_type="Anonymous")
            mock_get_anonymous.return_value = mock_claims

            client = TestClient(app_with_middleware)
            response = client.get("/test")

            assert response.status_code == 200
            assert response.json()["authenticated"] is False

            # Verify get_anonymous_claims was called
            mock_get_anonymous.assert_called_once()
