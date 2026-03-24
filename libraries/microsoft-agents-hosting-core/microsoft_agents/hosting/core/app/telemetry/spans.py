# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from opentelemetry.trace import Span
from microsoft_agents.activity import TurnContextProtocol
from microsoft_agents.hosting.core.telemetry import (
    AttributeMap,
    attributes,
    SimpleSpanWrapper,
    get_conversation_id,
)
from . import constants, metrics

class AppOnTurn(SimpleSpanWrapper):
    """Span for the entire app run, starting from when an activity is received in the adapter, until a response is sent back (if applicable). This span is meant to be a parent span for all other spans created during the processing of the activity, and can be used to correlate all telemetry for a given app run."""

    def __init__(self, turn_context: TurnContextProtocol):
        """Initializes the AppOnTurn SpanWrapper.
        
        :param turn_context: The TurnContext for the app run, used to extract attributes for the span
        """
        super().__init__(constants.SPAN_ON_TURN)
        self._turn_context = turn_context

    def _callback(self, span: Span, duration: float, error: Exception | None) -> None:
        """Callback function that is called when the span is ended. This is used to record metrics for the app run based on the outcome of the span."""
        if error is None:
            metrics.turn_total.add(1)
            metrics.turn_duration.record(
                duration,
                {
                    attributes.CONVERSATION_ID: (
                        get_conversation_id(self._turn_context.activity)
                    ),
                    attributes.ACTIVITY_CHANNEL_ID: self._turn_context.activity.channel_id or attributes.UNKNOWN,
                },
            )
        else:
            metrics.turn_errors.add(1)

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.CONVERSATION_ID: get_conversation_id(self._turn_context.activity),
            attributes.ACTIVITY_CHANNEL_ID: self._turn_context.activity.channel_id or attributes.UNKNOWN,
            attributes.SERVICE_URL: self._turn_context.activity.service_url,
        }
    
    def share(self, route_authorized: bool, route_matched: bool) -> None:
        """Shares the span context for this app run with downstream spans, and adds attributes related to routing decisions

        :param route_authorized: Whether the route for this app run was authorized
        :param route_matched: Whether the route for this app run was matched
        """
        if self._span is not None:
            self._span.set_attribute(attributes.ROUTE_AUTHORIZED, route_authorized)
            self._span.set_attribute(attributes.ROUTE_MATCHED, route_matched)

class AppRouteHandler(SimpleSpanWrapper):
    """Span for handling the routing logic. From selection, through authorization, and through the invocation of the route handler."""

    def __init__(self, turn_context: TurnContextProtocol):
        """Initializes the AppRouteHandler SpanWrapper."""
        super().__init__(constants.SPAN_ROUTE_HANDLER)
        self._turn_context = turn_context

    def _get_attributes(self) -> AttributeMap:
        """Gets attributes for the AppRouteHandler span, based on the activity being processed."""
        return {
            attributes.CONVERSATION_ID: get_conversation_id(self._turn_context.activity),
            attributes.ACTIVITY_CHANNEL_ID: self._turn_context.activity.channel_id or attributes.UNKNOWN,
            attributes.SERVICE_URL: self._turn_context.activity.service_url,
        }

class AppBeforeTurn(SimpleSpanWrapper):
    """Span for the logic that happens before the main turn processing. This is meant to capture telemetry for the pre-processing logic of the app run, and can be used to identify issues in the early stages of the app run before the main processing logic is invoked."""

    def __init__(self):
        """Initializes the AppBeforeTurn SpanWrapper."""
        super().__init__(constants.SPAN_BEFORE_TURN)

class AppAfterTurn(SimpleSpanWrapper):
    """Span for the logic that happens after the main turn processing. This is meant to capture telemetry for the post-processing logic of the app run, and can be used to identify issues in the later stages of the app run after the main processing logic is invoked."""

    def __init__(self):
        """Initializes the AppAfterTurn SpanWrapper."""
        super().__init__(constants.SPAN_AFTER_TURN)

class AppDownloadFiles(SimpleSpanWrapper):
    """Span for the logic related to downloading files in the app. This can be used to capture telemetry for file download operations, and to identify issues related to file downloads in the app."""

    def __init__(self, turn_context: TurnContextProtocol):
        """Initializes the AppDownloadFiles SpanWrapper."""
        super().__init__(constants.SPAN_DOWNLOAD_FILES)
        self._turn_context = turn_context

    def _get_attributes(self) -> AttributeMap:
        return {
            attributes.ATTACHMENT_COUNT: len(self._turn_context.activity.attachments or []),
        }