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

class _ConnectorSpanWrapper(SimpleSpanWrapper):
    """Base SpanWrapper for spans related to connector operations in the adapter. This is meant to be a base class for spans related to connector operations, such as creating a connector client or creating a user token, and can be used to share common functionality and attributes related to connector operations."""

    def __init__(self, span_name: str, *, conversation_id: str | None = None, activity_id: str | None = None):
        """Initializes the _ConnectorSpanWrapper span."""
        super().__init__(span_name)
        self._conversation_id = conversation_id
        self._activity_id = activity_id

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the connector operation based on the outcome of the span."""
        _metrics.connector_request_duration.record(duration)
        _metrics.connector_request_total.add(1)

    def _get_attributes(self) -> dict[str, str]:
        """Returns a dictionary of attributes to set on the span when it is started. This includes attributes related to the connector operation being performed."""
        attributes = {}
        if self._conversation_id is not None:
            attributes[constants.ATTR_CONVERSATION_ID] = self._conversation_id
        if self._activity_id is not None:
            attributes[constants.ATTR_ACTIVITY_ID] = self._activity_id
        return attributes
    
class ConnectorReplyToActivity(_ConnectorSpanWrapper):
    """Span for replying to an activity using the connector client in the adapter."""

    def __init__(self, conversation_id: str, activity_id: str):
        """Initializes the ConnectorReplyToActivity span."""
        super().__init__(constants.SPAN_CONNECTOR_REPLY_TO_ACTIVITY,
                         conversation_id=conversation_id, 
                         activity_id=activity_id)

class ConnectorSendToConversation(_ConnectorSpanWrapper):
    """Span for sending to a conversation using the connector client in the adapter."""

    def __init__(self, conversation_id: str, activity_id: str):
        """Initializes the ConnectorSendToConversation span."""
        super().__init__(constants.SPAN_CONNECTOR_SEND_TO_CONVERSATION,
                         conversation_id=conversation_id,
                         activity_id=activity_id)

class ConnectorUpdateActivity(_ConnectorSpanWrapper):
    """Span for updating an activity using the connector client in the adapter."""

    def __init__(self, conversation_id: str, activity_id: str):
        """Initializes the ConnectorUpdateActivity span."""
        super().__init__(constants.SPAN_CONNECTOR_UPDATE_ACTIVITY,
                         conversation_id=conversation_id,
                         activity_id=activity_id)

class ConnectorDeleteActivity(_ConnectorSpanWrapper):
    """Span for deleting an activity using the connector client in the adapter."""

    def __init__(self, conversation_id: str, activity_id: str):
        """Initializes the ConnectorDeleteActivity span."""
        super().__init__(constants.SPAN_CONNECTOR_DELETE_ACTIVITY,
                         conversation_id=conversation_id,
                         activity_id=activity_id)

class ConnectorCreateConversation(_ConnectorSpanWrapper):
    """Span for creating a conversation using the connector client in the adapter."""

    def __init__(self):
        """Initializes the ConnectorCreateConversation span."""
        super().__init__(constants.SPAN_CONNECTOR_CREATE_CONVERSATION)

class ConnectorGetConversations(_ConnectorSpanWrapper):
    """Span for getting conversations using the connector client in the adapter."""

    def __init__(self):
        """Initializes the ConnectorGetConversations span."""
        super().__init__(constants.SPAN_CONNECTOR_GET_CONVERSATIONS)

class ConnectorGetConversationMembers(_ConnectorSpanWrapper):
    """Span for getting conversation members using the connector client in the adapter."""

    def __init__(self):
        """Initializes the ConnectorGetConversationMembers span."""
        super().__init__(constants.SPAN_CONNECTOR_GET_CONVERSATION_MEMBERS)

class ConnectorUploadAttachment(_ConnectorSpanWrapper):
    """Span for uploading an attachment using the connector client in the adapter."""

    def __init__(self, conversation_id: str):
        """Initializes the ConnectorUploadAttachment span."""
        super().__init__(constants.SPAN_CONNECTOR_UPLOAD_ATTACHMENT,
                         conversation_id=conversation_id)
        
class ConnectorGetAttachment(_ConnectorSpanWrapper):
    """Span for getting an attachment using the connector client in the adapter."""

    def __init__(self, attachment_id: str):
        """Initializes the ConnectorGetAttachment span."""
        super().__init__(constants.SPAN_CONNECTOR_GET_ATTACHMENT)
        self._attachment_id = attachment_id

    def _get_attributes(self) -> AttributeMap:
        attributes = super()._get_attributes()
        attributes[constants.ATTR_ATTACHMENT_ID] = self._attachment_id
        return attributes
