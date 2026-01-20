# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from microsoft_agents.hosting.core.authorization.claims_identity import ClaimsIdentity
from microsoft_agents.hosting.core.authorization.authentication_constants import (
    AuthenticationConstants,
)


class TestClaimsIdentity:
    """Unit tests for ClaimsIdentity class, specifically testing get_token_scope method."""

    def test_get_token_scope_agent_claim_with_app_id(self):
        """
        Test get_token_scope returns correct format for agent claims.
        When is_agent_claim() returns True, the scope should be "{app_id}/.default"
        """
        # Setup claims that will make is_agent_claim() return True
        # Requirements for agent claim:
        # - version claim exists
        # - audience claim exists and is not AGENTS_SDK_TOKEN_ISSUER
        # - get_outgoing_app_id() returns a value
        # - app_id != audience
        app_id = "test-app-id-123"
        audience = "different-audience-456"
        
        claims = {
            AuthenticationConstants.VERSION_CLAIM: "2.0",
            AuthenticationConstants.AUDIENCE_CLAIM: audience,
            AuthenticationConstants.AUTHORIZED_PARTY: app_id,  # Used for version 2.0
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify this is an agent claim
        assert claims_identity.is_agent_claim() is True
        
        # Test get_token_scope
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{app_id}/.default"

    def test_get_token_scope_non_agent_claim(self):
        """
        Test get_token_scope returns correct format for non-agent claims.
        When is_agent_claim() returns False, the scope should be 
        "https://api.botframework.com/.default"
        """
        # Setup claims that will make is_agent_claim() return False
        # This can happen when:
        # - version claim is missing
        # - audience is AGENTS_SDK_TOKEN_ISSUER
        # - app_id equals audience
        app_id = "test-app-id-789"
        
        claims = {
            AuthenticationConstants.VERSION_CLAIM: "1.0",
            AuthenticationConstants.AUDIENCE_CLAIM: AuthenticationConstants.AGENTS_SDK_TOKEN_ISSUER,
            AuthenticationConstants.APP_ID_CLAIM: app_id,  # Used for version 1.0
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify this is NOT an agent claim
        assert claims_identity.is_agent_claim() is False
        
        # Test get_token_scope
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{AuthenticationConstants.AGENTS_SDK_SCOPE}/.default"

    def test_get_token_scope_edge_case_no_outgoing_app_id(self):
        """
        Test get_token_scope behavior when get_outgoing_app_id returns None.
        This is an edge case where the app_id is not present in the claims.
        """
        # Setup claims with no app_id information
        claims = {
            AuthenticationConstants.VERSION_CLAIM: "2.0",
            AuthenticationConstants.AUDIENCE_CLAIM: "some-audience",
            # No APP_ID_CLAIM or AUTHORIZED_PARTY
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify get_outgoing_app_id returns None
        assert claims_identity.get_outgoing_app_id() is None
        
        # Verify is_agent_claim returns False (because get_outgoing_app_id is None)
        assert claims_identity.is_agent_claim() is False
        
        # Test get_token_scope - should fall back to AGENTS_SDK_SCOPE
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{AuthenticationConstants.AGENTS_SDK_SCOPE}/.default"

    def test_get_token_scope_edge_case_missing_version(self):
        """
        Test get_token_scope when version claim is missing.
        This should result in is_agent_claim() returning False.
        """
        app_id = "test-app-id-no-version"
        
        claims = {
            # No VERSION_CLAIM
            AuthenticationConstants.AUDIENCE_CLAIM: "some-audience",
            AuthenticationConstants.APP_ID_CLAIM: app_id,
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify is_agent_claim returns False (because version is missing)
        assert claims_identity.is_agent_claim() is False
        
        # Test get_token_scope
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{AuthenticationConstants.AGENTS_SDK_SCOPE}/.default"

    def test_get_token_scope_agent_claim_version_1_0(self):
        """
        Test get_token_scope with version 1.0 token that qualifies as agent claim.
        """
        app_id = "test-app-id-v1"
        audience = "different-audience-v1"
        
        claims = {
            AuthenticationConstants.VERSION_CLAIM: "1.0",
            AuthenticationConstants.AUDIENCE_CLAIM: audience,
            AuthenticationConstants.APP_ID_CLAIM: app_id,  # Used for version 1.0
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify this is an agent claim (app_id != audience)
        assert claims_identity.is_agent_claim() is True
        
        # Test get_token_scope
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{app_id}/.default"

    def test_get_token_scope_non_agent_claim_same_app_id_and_audience(self):
        """
        Test get_token_scope when app_id equals audience.
        This should result in is_agent_claim() returning False.
        """
        app_id = "same-id-for-both"
        
        claims = {
            AuthenticationConstants.VERSION_CLAIM: "2.0",
            AuthenticationConstants.AUDIENCE_CLAIM: app_id,  # Same as app_id
            AuthenticationConstants.AUTHORIZED_PARTY: app_id,  # Same as audience
        }
        
        claims_identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=True,
            authentication_type="Bearer"
        )
        
        # Verify is_agent_claim returns False (because app_id == audience)
        assert claims_identity.is_agent_claim() is False
        
        # Test get_token_scope
        result = claims_identity.get_token_scope()
        
        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == f"{AuthenticationConstants.AGENTS_SDK_SCOPE}/.default"
