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
from . import constants, metrics


class _AuthenticationSpanWrapper(SimpleSpanWrapper):
    """Base SpanWrapper for spans related to authentication operations.

    This is meant to be a base class for spans related to authentication operations, such as retrieving or validating tokens,
    and can be used to share common functionality and attributes
    """

    def __init__(self, span_name: str):
        """Initializes the _StorageSpanWrapper span."""
        super().__init__(span_name)

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span ends. This function can be used to set additional attributes or record exceptions based on the outcome of the operation being traced."""


class GetAccessToken(_AuthenticationSpanWrapper):
    """Span wrapper for the operation of retrieving an access token."""

    def __init__(self, scopes: list[str], auth_type: str):
        """Initializes the GetAccessToken span with the specified authentication scope and type."""
        super().__init__(constants.SPAN_GET_ACCESS_TOKEN)
        self._scopes = scopes
        self._auth_type = auth_type

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to be set on the span. This includes the authentication scope and type."""
        return {
            attributes.AUTH_SCOPES: format_scopes(self._scopes),
            attributes.AUTH_TYPE: self._auth_type,
        }


class AcquireTokenOnBehalfOf(_AuthenticationSpanWrapper):
    """Span wrapper for the operation of acquiring a token on behalf of a user."""

    def __init__(self, scopes: list[str]):
        """Initializes the AcquireTokenOnBehalfOf span with the specified authentication scope."""
        super().__init__(constants.SPAN_ACQUIRE_TOKEN_ON_BEHALF_OF)
        self._scopes = scopes

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to be set on the span. This includes the authentication scope."""
        return {
            attributes.AUTH_SCOPES: format_scopes(self._scopes),
        }


class GetAgenticInstanceToken(_AuthenticationSpanWrapper):
    """Span wrapper for the operation of retrieving an agentic instance token."""

    def __init__(self, agentic_instance_id: str):
        """Initializes the GetAgenticInstanceToken span with the specified agentic instance ID."""
        super().__init__(constants.SPAN_GET_AGENTIC_INSTANCE_TOKEN)
        self._agentic_instance_id = agentic_instance_id

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to be set on the span. This includes the agentic instance ID."""
        return {
            attributes.AGENTIC_INSTANCE_ID: self._agentic_instance_id,
        }


class GetAgenticUserToken(_AuthenticationSpanWrapper):
    """Span wrapper for the operation of retrieving an agentic user token."""

    def __init__(
        self, agentic_instance_id: str, agentic_user_id: str, scopes: list[str]
    ):
        """Initializes the GetAgenticUserToken span with the specified agentic instance ID, user ID, and authentication scopes."""
        super().__init__(constants.SPAN_GET_AGENTIC_USER_TOKEN)
        self._agentic_instance_id = agentic_instance_id
        self._agentic_user_id = agentic_user_id
        self._scopes = scopes

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to be set on the span. This includes the agentic instance ID, user ID, and authentication scopes."""
        return {
            attributes.AGENTIC_INSTANCE_ID: self._agentic_instance_id,
            attributes.AGENTIC_USER_ID: self._agentic_user_id,
            attributes.AUTH_SCOPES: format_scopes(self._scopes),
        }
