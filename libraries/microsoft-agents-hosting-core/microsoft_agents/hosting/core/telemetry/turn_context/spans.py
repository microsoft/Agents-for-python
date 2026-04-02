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


class TurnContextSendActivity(SimpleSpanWrapper):
    """Span wrapper for sending an activity within a turn context."""

    def __init__(self, turn_context: TurnContextProtocol):
        super().__init__(constants.SPAN_TURN_SEND_ACTIVITY)
        self._turn_context = turn_context

    def _get_attributes(self) -> AttributeMap:
        activity = self._turn_context.activity
        return {
            attributes.CONVERSATION_ID: get_conversation_id(activity),
        }
