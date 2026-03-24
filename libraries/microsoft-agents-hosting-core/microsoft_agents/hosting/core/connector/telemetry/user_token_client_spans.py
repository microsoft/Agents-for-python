# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span

from microsoft_agents.hosting.core.telemetry import attributes
from ._request_span_wrapper import _RequestSpanWrapper
from . import metrics, constants


class _UserTokenClientSpanWrapper(_RequestSpanWrapper):
    """Base SpanWrapper for spans related to user token client operations in the adapter. This is meant to be a base class for spans related to user token client operations, such as creating a user token, and can be used to share common functionality and attributes related to user token client operations."""

    def __init__(
        self,
        span_name: str,
        *,
        connection_name: str | None = None,
        user_id: str | None = None,
        channel_id: str | None = None,
    ):
        """Initializes the _UserTokenClientSpanWrapper span."""
        super().__init__(span_name)
        self._connection_name = connection_name or attributes.UNKNOWN
        self._user_id = user_id or attributes.UNKNOWN
        self._channel_id = channel_id or attributes

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the user token client operation based on the outcome of the span."""
        attrs = self._get_request_attributes()
        metrics.user_token_client_request_duration.record(duration, attributes=attrs)
        metrics.user_token_client_request_count.add(1, attributes=attrs)

    def _get_attributes(self) -> dict[str, str]:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the user token client operation being performed.

        NOTE: a dict is the annotated return type to allow child classes to add additional attributes.
        """
        attr_dict = {}
        if self._connection_name is not None:
            attr_dict[attributes.CONNECTION_NAME] = self._connection_name
        if self._user_id is not None:
            attr_dict[attributes.USER_ID] = self._user_id
        if self._channel_id is not None:
            attr_dict[attributes.ACTIVITY_CHANNEL_ID] = self._channel_id
        return attr_dict


class GetUserToken(_UserTokenClientSpanWrapper):
    """Span for getting a user token using the user token client in the adapter."""

    def __init__(
        self, connection_name: str, user_id: str, channel_id: str | None = None
    ):
        """Initializes the GetUserToken span."""
        super().__init__(
            constants.SPAN_GET_USER_TOKEN,
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
        )


class SignOut(_UserTokenClientSpanWrapper):
    """Span for signing out a user using the user token client in the adapter."""

    def __init__(
        self, connection_name: str, user_id: str, channel_id: str | None = None
    ):
        """Initializes the SignOut span."""
        super().__init__(
            constants.SPAN_SIGN_OUT,
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
        )


class GetSignInResource(_UserTokenClientSpanWrapper):
    """Span for getting a sign-in resource using the user token client in the adapter."""

    def __init__(self):
        """Initializes the GetSignInResource span."""
        super().__init__(constants.SPAN_GET_SIGN_IN_RESOURCE)


class ExchangeToken(_UserTokenClientSpanWrapper):
    """Span for exchanging a token using the user token client in the adapter."""

    def __init__(
        self, connection_name: str, user_id: str, channel_id: str | None = None
    ):
        """Initializes the ExchangeToken span."""
        super().__init__(
            constants.SPAN_EXCHANGE_TOKEN,
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
        )


class GetTokenOrSignInResource(_UserTokenClientSpanWrapper):
    """Span for getting a token or sign-in resource using the user token client in the adapter."""

    def __init__(
        self, connection_name: str, user_id: str, channel_id: str | None = None
    ):
        """Initializes the GetTokenOrSignInResource span."""
        super().__init__(
            constants.SPAN_GET_TOKEN_OR_SIGN_IN_RESOURCE,
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
        )


class GetTokenStatus(_UserTokenClientSpanWrapper):
    """Span for getting token status using the user token client in the adapter."""

    def __init__(self, user_id: str, channel_id: str | None = None):
        """Initializes the GetTokenStatus span."""
        super().__init__(
            constants.SPAN_GET_TOKEN_STATUS, user_id=user_id, channel_id=channel_id
        )


class GetAadTokens(_UserTokenClientSpanWrapper):
    """Span for getting AAD tokens using the user token client in the adapter."""

    def __init__(
        self, connection_name: str, user_id: str, channel_id: str | None = None
    ):
        """Initializes the GetAadTokens span."""
        super().__init__(
            constants.SPAN_GET_AAD_TOKENS,
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
        )
