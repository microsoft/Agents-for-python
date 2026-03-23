from __future__ import annotations

from ..core import constants, AttributeMap
from opentelemetry.trace import Span
from microsoft_agents.activity import Activity

from ..core import (
    constants,
    AttributeMap,
    SimpleSpanWrapper,
)
from ..core.utils import get_conversation_id, get_delivery_mode, format_scopes
from .. import _metrics

class AdapterProcess(SimpleSpanWrapper):
    """Span for processing an incoming activity in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterProcess SpanWrapper."""
        super().__init__(constants.SPAN_ADAPTER_PROCESS)
        self._activity = activity

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the adapter processing based on the outcome of the span."""
        _metrics.adapter_process_duration.record(duration)

    def _get_attributes(self) -> AttributeMap:
        return {
            constants.ATTR_ACTIVITY_TYPE: self._activity.type,
            constants.ATTR_ACTIVITY_CHANNEL_ID: self._activity.channel_id or constants.UNKNOWN,
            constants.ATTR_ACTIVITY_DELIVERY_MODE: get_delivery_mode(self._activity),
            constants.ATTR_CONVERSATION_ID: get_conversation_id(self._activity),
            constants.ATTR_IS_AGENTIC_REQUEST: self._activity.is_agentic_request(),
        }

class AdapterSendActivities(SimpleSpanWrapper):
    """Span for sending activities in the adapter."""

    def __init__(self, activities: list[Activity]):
        """Initializes the AdapterSendActivities span."""
        super().__init__(constants.SPAN_ADAPTER_SEND_ACTIVITIES)
        self._activities = activities

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activities being sent."""
        return {
            constants.ATTR_ACTIVITY_COUNT: len(self._activities),
            constants.ATTR_CONVERSATION_ID: (
                get_conversation_id(self._activities[0])
                if self._activities else constants.UNKNOWN
            ),
        }

class AdapterUpdateActivity(SimpleSpanWrapper):
    """Span for updating an activity in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterUpdateActivity span."""
        super().__init__(constants.SPAN_ADAPTER_UPDATE_ACTIVITY)
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activity being updated."""
        return {
            constants.ATTR_ACTIVITY_ID: self._activity.id or constants.UNKNOWN,
            constants.ATTR_CONVERSATION_ID: get_conversation_id(self._activity),
        }

class AdapterDeleteActivity(SimpleSpanWrapper):
    """Span for deleting an activity in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterDeleteActivity span."""
        super().__init__(constants.SPAN_ADAPTER_DELETE_ACTIVITY)
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the activity being deleted."""
        return {
            constants.ATTR_ACTIVITY_ID: self._activity.id or constants.UNKNOWN,
            constants.ATTR_CONVERSATION_ID: get_conversation_id(self._activity),
        }

class AdapterContinueConversation(SimpleSpanWrapper):
    """Span for continuing a conversation in the adapter."""

    def __init__(self, activity: Activity):
        """Initializes the AdapterContinueConversation span."""
        super().__init__(constants.SPAN_ADAPTER_CONTINUE_CONVERSATION)
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the conversation being continued."""
        return {
            constants.ATTR_APP_ID: self._activity.recipient.id if self._activity.recipient else constants.UNKNOWN,
            constants.ATTR_CONVERSATION_ID: get_conversation_id(self._activity),
            constants.ATTR_IS_AGENTIC_REQUEST: self._activity.is_agentic_request(),
        }

class AdapterCreateUserTokenClient(SimpleSpanWrapper):
    """Span for creating a user token in the adapter."""

    def __init__(self, token_service_endpoint: str, scopes: list[str] | None):
        """Initializes the AdapterCreateUserToken span."""
        super().__init__(constants.SPAN_ADAPTER_CREATE_USER_TOKEN_CLIENT)
        self._token_service_endpoint = token_service_endpoint
        self._scopes = scopes

    def _get_attributes(self) -> AttributeMap:
        """Starts the AdapterCreateUserToken span, and sets attributes related to the user token being created."""
        return {
                    constants.ATTR_TOKEN_SERVICE_ENDPOINT: self._token_service_endpoint,
                    constants.ATTR_AUTH_SCOPES: format_scopes(self._scopes),
        }

class AdapterCreateConnectorClient(SimpleSpanWrapper):
    """Span for creating a connector client in the adapter."""

    def __init__(self, service_url: str, scopes: list[str] | None, is_agentic_request: bool):
        """Initializes the AdapterCreateConnectorClient span."""
        super().__init__(constants.SPAN_ADAPTER_CREATE_CONNECTOR_CLIENT)
        self._service_url = service_url
        self._scopes = scopes
        self._is_agentic_request = is_agentic_request

    def _get_attributes(self) -> AttributeMap:
        """Starts the AdapterCreateConnectorClient span, and sets attributes related to the connector client being created."""
        return {
            constants.ATTR_SERVICE_URL: self._service_url,
            constants.ATTR_AUTH_SCOPES: format_scopes(self._scopes),
            constants.ATTR_IS_AGENTIC_REQUEST: self._is_agentic_request,
        }