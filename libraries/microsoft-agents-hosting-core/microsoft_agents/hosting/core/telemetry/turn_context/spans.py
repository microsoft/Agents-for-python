# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from microsoft_agents.activity import TurnContextProtocol
from microsoft_agents.hosting.core.telemetry import (
    AttributeMap,
    SimpleSpanWrapper,
    attributes,
    get_conversation_id,
)
from . import constants


class _TurnContextSpanWrapper(SimpleSpanWrapper):
    """Base span wrapper for TurnContext operations"""

    def __init__(self, span_name: str, turn_context: TurnContextProtocol):
        """Initializes the span wrapper with the given span name and turn context."""
        super().__init__(span_name)
        self._turn_context = turn_context

    def _get_attributes(self) -> AttributeMap:
        activity = self._turn_context.activity
        return {
            attributes.CONVERSATION_ID: get_conversation_id(activity),
        }


class TurnContextSendActivity(_TurnContextSpanWrapper):
    """Span wrapper for sending an activity within a turn context."""

    def __init__(self, turn_context: TurnContextProtocol):
        super().__init__(constants.SPAN_TURN_SEND_ACTIVITY, turn_context)


class TurnContextUpdateActivity(_TurnContextSpanWrapper):
    """Span wrapper for updating an activity within a turn context."""

    def __init__(self, turn_context: TurnContextProtocol):
        super().__init__(constants.SPAN_TURN_UPDATE_ACTIVITY, turn_context)


class TurnContextDeleteActivity(_TurnContextSpanWrapper):
    """Span wrapper for deleting an activity within a turn context."""

    def __init__(self, turn_context: TurnContextProtocol):
        super().__init__(constants.SPAN_TURN_DELETE_ACTIVITY, turn_context)
