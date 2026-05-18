# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span
from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core.telemetry import (
    AttributeMap,
    attributes,
    SimpleSpanWrapper,
)
from . import constants
from ..create_conversation_options import CreateConversationOptions


class ProactiveStoreConversation(SimpleSpanWrapper):
    """Span for storing a conversation reference in proactive scenarios, starting from when the store operation is initiated until it is completed. This span can be used to correlate telemetry related to storing conversation references in proactive scenarios."""

    def __init__(self, conversation_id: str):
        """Initializes the ProactiveStoreConversation SpanWrapper.

        :param conversation_id: The ID of the conversation being stored, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_STORE_CONVERSATION)
        self._conversation_id = conversation_id

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: self._conversation_id or attributes.UNKNOWN,
        }


class ProactiveGetConversation(SimpleSpanWrapper):
    """Span for getting a conversation reference in proactive scenarios, starting from when the get operation is initiated until it is completed. This span can be used to correlate telemetry related to getting conversation references in proactive scenarios."""

    def __init__(self, conversation_id: str):
        """Initializes the ProactiveGetConversation SpanWrapper.

        :param conversation_id: The ID of the conversation being retrieved, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_GET_CONVERSATION)
        self._conversation_id = conversation_id
        self._found: bool | None = None

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: self._conversation_id or attributes.UNKNOWN,
            attributes.CONVERSATION_FOUND: (
                self._found if self._found is not None else attributes.UNKNOWN
            ),
        }

    def share(self, found: bool) -> None:
        """Records to the span whether the conversation being retrieved was found.

        :param found: Whether the conversation being retrieved was found
        """
        self._found = found


class ProactiveDeleteConversation(SimpleSpanWrapper):
    """Span for deleting a conversation reference in proactive scenarios, starting from when the delete operation is initiated until it is completed. This span can be used to correlate telemetry related to deleting conversation references in proactive scenarios."""

    def __init__(self, conversation_id: str):
        """Initializes the ProactiveDeleteConversation SpanWrapper.

        :param conversation_id: The ID of the conversation being deleted, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_DELETE_CONVERSATION)
        self._conversation_id = conversation_id

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: self._conversation_id or attributes.UNKNOWN,
        }


class ProactiveSendActivity(SimpleSpanWrapper):
    """Span for sending an activity in proactive scenarios, starting from when the send operation is initiated until it is completed. This span can be used to correlate telemetry related to sending activities in proactive scenarios."""

    def __init__(self, conversation_id: str, activity: Activity):
        """Initializes the ProactiveSendActivity SpanWrapper.

        :param conversation_id: The ID of the conversation the activity is being sent to, used to extract attributes for the span
        :param activity: The activity being sent, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_SEND_ACTIVITY)
        self._conversation_id = conversation_id
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: self._conversation_id or attributes.UNKNOWN,
            attributes.ACTIVITY_TYPE: self._activity.type or attributes.UNKNOWN,
            attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
            or attributes.UNKNOWN,
        }


class ProactiveContinueConversation(SimpleSpanWrapper):
    """Span for continuing a conversation in proactive scenarios, starting from when the continue operation is initiated until it is completed. This span can be used to correlate telemetry related to continuing conversations in proactive scenarios."""

    def __init__(self, conversation_id: str, activity: Activity):
        """Initializes the ProactiveContinueConversation SpanWrapper.

        :param conversation_id: The ID of the conversation being continued, used to extract attributes for the span
        :param activity: The activity being sent, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_CONTINUE_CONVERSATION)
        self._conversation_id = conversation_id
        self._activity = activity

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: self._conversation_id or attributes.UNKNOWN,
            attributes.ACTIVITY_TYPE: self._activity.type or attributes.UNKNOWN,
            attributes.ACTIVITY_CHANNEL_ID: self._activity.channel_id
            or attributes.UNKNOWN,
        }


class ProactiveCreateConversation(SimpleSpanWrapper):
    """Span for creating a conversation in proactive scenarios, starting from when the create operation is initiated until it is completed. This span can be used to correlate telemetry related to creating conversations in proactive scenarios."""

    def __init__(self, options: CreateConversationOptions):
        """Initializes the ProactiveCreateConversation SpanWrapper.

        :param options: The options used to create the conversation, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_CREATE_CONVERSATION)
        self._channel_id = options.channel_id
        self._members_count: str | int = (
            len(options.parameters.members)
            if options.parameters and options.parameters.members
            else attributes.UNKNOWN
        )

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.ACTIVITY_CHANNEL_ID: self._channel_id,
            attributes.MEMBERS_COUNT: self._members_count,
        }
