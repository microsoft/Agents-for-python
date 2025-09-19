"""
Testing utilities for authorization functionality

This module provides mock implementations and helper classes for testing authorization,
authentication, and token management scenarios. It includes test doubles for token
providers, connection managers, and authorization handlers that can be configured
to simulate various authentication states and flow conditions.
"""

from microsoft_agents.hosting.core import (
    Connections,
    AccessTokenProviderBase,
    AuthHandler,
    Authorization,
    MemoryStorage,
    OAuthFlow,
)
from typing import Dict, Union
from microsoft_agents.hosting.core.authorization.agent_auth_configuration import (
    AgentAuthConfiguration,
)
from microsoft_agents.hosting.core.authorization.claims_identity import ClaimsIdentity

from microsoft_agents.activity import TokenResponse

from unittest.mock import Mock, AsyncMock


def create_test_auth_handler(
    name: str, obo: bool = False, title: str = None, text: str = None
):
    """
    Creates a test AuthHandler instance with standardized connection names.

    This helper function simplifies the creation of AuthHandler objects for testing
    by automatically generating connection names based on the provided name and
    optionally including On-Behalf-Of (OBO) connection configuration.

    Args:
        name: Base name for the auth handler, used to generate connection names
        obo: Whether to include On-Behalf-Of connection configuration
        title: Optional title for the auth handler
        text: Optional descriptive text for the auth handler

    Returns:
        AuthHandler: Configured auth handler instance with test-friendly connection names
    """
    return AuthHandler(
        name,
        abs_oauth_connection_name=f"{name}-abs-connection",
        obo_connection_name=f"{name}-obo-connection" if obo else None,
        title=title,
        text=text,
    )
