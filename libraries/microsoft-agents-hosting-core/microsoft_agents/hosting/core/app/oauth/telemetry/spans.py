# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span

from microsoft_agents.hosting.core.telemetry import (
    attributes,
    AttributeMap,
    SimpleSpanWrapper,
    format_scopes,
)
from . import constants

class _AuthorizationSpanWrapper(SimpleSpanWrapper):
    """Base SpanWrapper for spans related to authorization operations.
    
    This is meant to be a base class for spans related to authorization operations,
    and can be used to share common functionality and attributes
    """

    def __init__(
        self,
        span_name: str,
        auth_handler_id: str,
        connection_name: str | None = None,
        scopes: list[str] | None = None,
    ):
        """Initializes the _StorageSpanWrapper span."""
        super().__init__(span_name)
        self._auth_handler_id = auth_handler_id
        self._connection_name = connection_name
        self._scopes = scopes

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span ends."""

    def _get_attributes(self) -> dict[str, str]:
        """Gets the attributes to be added to the span."""
        attr_dict = {
            attributes.AUTH_HANDLER_ID: self._auth_handler_id,
            attributes.CONNECTION_NAME: self._connection_name or attributes.UNKNOWN,
        }
        if self._scopes is not None:
            attr_dict[attributes.AUTH_SCOPES] = format_scopes(self._scopes)
        return attr_dict


class AgenticToken(_AuthorizationSpanWrapper):
    """Span wrapper for agentic token operations."""

    def __init__(
        self,
        auth_handler_id: str,
        connection_name: str | None,
        scopes: list[str] | None,
    ):
        """Initializes the AgenticToken span."""
        super().__init__(
            constants.AGENTIC_TOKEN,
            auth_handler_id,
            connection_name,
            scopes,
        )

class AzureBotToken(_AuthorizationSpanWrapper):
    """Span wrapper for azure bot token operations."""

    def __init__(
        self,
        auth_handler_id: str,
        connection_name: str | None,
        scopes: list[str] | None,
    ):
        """Initializes the AzureBotToken span."""
        super().__init__(
            constants.AZURE_BOT_TOKEN,
            auth_handler_id,
            connection_name,
            scopes,
        )

class AzureBotSignIn(_AuthorizationSpanWrapper):
    """Span wrapper for azure bot sign in operations."""

    def __init__(
        self,
        auth_handler_id: str,
        connection_name: str | None,
        scopes: list[str] | None,
    ):
        """Initializes the AzureBotSignIn span."""
        super().__init__(
            constants.AZURE_BOT_SIGN_IN,
            auth_handler_id,
            connection_name,
            scopes,
        )

class AzureBotSignOut(_AuthorizationSpanWrapper):
    """Span wrapper for azure bot sign out operations."""

    def __init__(self,  auth_handler_id: str):
        """Initializes the AzureBotSignOut span."""
        super().__init__(
            constants.AZURE_BOT_SIGN_OUT,
            auth_handler_id,
        )