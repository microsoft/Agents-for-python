# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span
from microsoft_agents.activity import Activity

from microsoft_agents.hosting.core.telemetry import (
    AttributeMap,
    SimpleSpanWrapper,
    get_conversation_id,
    get_delivery_mode,
    format_scopes,
    attributes,
)
from . import constants, metrics


class AdapterProcess(SimpleSpanWrapper):
    """Span for processing an incoming activity in the adapter."""

    def __init__(self, activity: Activity | None = None):
        """Initializes the AdapterProcess SpanWrapper."""
        super().__init__(constants.SPAN_PROCESS)
        self._activity: Activity | None = activity

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the adapter processing based on the outcome of the span."""
        if self._activity is None:
            attrs = {
                attributes.ACTIVITY_TYPE: attributes.UNKNOWN,
                attributes.ACTIVITY_CHANNEL_ID: attributes.UNKNOWN,
            }
        else:
            attrs = {
                attributes.ACTIVITY_TYPE: self._activity.type,
                attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
                or attributes.UNKNOWN,
            }
        metrics.adapter_process_duration.record(duration, attributes=attrs)
        metrics.activities_received.add(1, attributes=attrs)

    def _get_attributes(self) -> AttributeMap:
        if self._activity is None:
            return {}
        return {
            attributes.ACTIVITY_TYPE: self._activity.type,
            attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
            or attributes.UNKNOWN,
            attributes.ACTIVITY_DELIVERY_MODE: get_delivery_mode(self._activity),
            attributes.CONVERSATION_ID: get_conversation_id(self._activity),
            attributes.IS_AGENTIC: self._activity.is_agentic_request(),
        }

    def share(self, *, activity: Activity) -> None:
        """Shares the activity being processed with the span, so that it can be used in the callback to record metrics."""
        self._activity = activity


class AdapterSendActivities(SimpleSpanWrapper):
    """Span for sending activities in the adapter."""

    def __init__(self, activities: list[Activity]):
        """Initializes the AdapterSendActivities span."""
        super().__init__(constants.SPAN_SEND_ACTIVITIES)
        self._activities = activities

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        for act in self._activities:
            metrics.activities_sent.add(
                1,
                attributes={
                    attributes.ACTIVITY_TYPE: act.type,
                    attributes.ACTIVITY_CHANNEL_ID: act.channel_id
                    or attributes.UNKNOWN,
                },
            )

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activities being sent."""
        return {
            attributes.ACTIVITY_COUNT: len(self._activities),
            attributes.CONVERSATION_ID: (
                get_conversation_id(self._activities[0])
                if self._activities
                else attributes.UNKNOWN
            ),
        }


class AdapterUpdateActivity(SimpleSpanWrapper):
    """Span for updating an activity in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterUpdateActivity span."""
        super().__init__(constants.SPAN_UPDATE_ACTIVITY)
        self._activity = activity

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        metrics.activities_updated.add(
            1,
            attributes={
                attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
                or attributes.UNKNOWN,
            },
        )

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activity being updated."""
        return {
            attributes.ACTIVITY_ID: self._activity.id or attributes.UNKNOWN,
            attributes.CONVERSATION_ID: get_conversation_id(self._activity),
        }


class AdapterDeleteActivity(SimpleSpanWrapper):
    """Span for deleting an activity in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterDeleteActivity span."""
        super().__init__(constants.SPAN_DELETE_ACTIVITY)
        self._activity = activity

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        metrics.activities_deleted.add(
            1,
            attributes={
                attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
                or attributes.UNKNOWN,
            },
        )

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activity being deleted."""
        return {
            attributes.ACTIVITY_ID: self._activity.id or attributes.UNKNOWN,
            attributes.CONVERSATION_ID: get_conversation_id(self._activity),
        }


class AdapterContinueConversation(SimpleSpanWrapper):
    """Span for continuing a conversation in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterContinueConversation span."""
        super().__init__(constants.SPAN_CONTINUE_CONVERSATION)
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the conversation being continued."""
        return {
            attributes.APP_ID: (
                self._activity.recipient.id
                if self._activity.recipient
                else attributes.UNKNOWN
            ),
            attributes.CONVERSATION_ID: get_conversation_id(self._activity),
            attributes.IS_AGENTIC: self._activity.is_agentic_request(),
        }


class AdapterCreateUserTokenClient(SimpleSpanWrapper):
    """Span for creating a user token in the adapter."""

    def __init__(self, token_service_endpoint: str, scopes: list[str] | None):
        """Initializes the AdapterCreateUserToken span."""
        super().__init__(constants.SPAN_CREATE_USER_TOKEN_CLIENT)
        self._token_service_endpoint = token_service_endpoint
        self._scopes = scopes

    def _get_attributes(self) -> AttributeMap:
        """Starts the AdapterCreateUserToken span, and sets attributes related to the user token being created."""
        return {
            attributes.TOKEN_SERVICE_ENDPOINT: self._token_service_endpoint,
            attributes.AUTH_SCOPES: format_scopes(self._scopes),
        }


class AdapterCreateConnectorClient(SimpleSpanWrapper):
    """Span for creating a connector client in the adapter."""

    def __init__(
        self, service_url: str, scopes: list[str] | None, is_agentic_request: bool
    ):
        """Initializes the AdapterCreateConnectorClient span."""
        super().__init__(constants.SPAN_CREATE_CONNECTOR_CLIENT)
        self._service_url = service_url
        self._scopes = scopes
        self._is_agentic_request = is_agentic_request

    def _get_attributes(self) -> AttributeMap:
        """Starts the AdapterCreateConnectorClient span, and sets attributes related to the connector client being created."""
        return {
            attributes.SERVICE_URL: self._service_url,
            attributes.AUTH_SCOPES: format_scopes(self._scopes),
            attributes.IS_AGENTIC: self._is_agentic_request,
        }


class AdapterWriteResponse(SimpleSpanWrapper):
    """Span for writing an InvokeResponse in the adapter. This captures the handling of expectReplies, invoke, and streaming"""

    def __init__(self, activity: Activity):
        """Initializes the AdapterWriteResponse span."""
        super().__init__(constants.SPAN_WRITE_RESPONSE)
        self._activity = activity

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        metrics.activities_sent.add(
            1,
            attributes={
                attributes.ACTIVITY_TYPE: self._activity.type,
                attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
                or attributes.UNKNOWN,
            },
        )

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activities being sent."""
        return {
            attributes.CONVERSATION_ID: get_conversation_id(self._activity),
        }
