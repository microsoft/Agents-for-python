from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry.trace import Span

from microsoft_agents.activity import Activity, TurnContextProtocol

from . import _metrics, constants
from ._agents_telemetry import agents_telemetry, _format_scopes

#
# Adapter
#

def _get_conversation_id(activity: Activity) -> str:
    return activity.conversation.id if activity.conversation else "unknown"

@contextmanager
def start_span_adapter_process(activity: Activity) -> Iterator[None]:
    """Context manager for reording adapter process call"""

    def callback(span: Span, duration: float, error: Exception | None):
        _metrics.adapter_process_duration.record(duration)

    with agents_telemetry.start_timed_span(
        constants.SPAN_ADAPTER_PROCESS,
        callback=callback
    ) as span:
        span.set_attributes({
            constants.ATTR_ACTIVITY_TYPE: activity.type,
            constants.ATTR_ACTIVITY_CHANNEL_ID: activity.channel_id or constants.UNKNOWN,
            constants.ATTR_ACTIVITY_DELIVERY_MODE: activity.delivery_mode,
            constants.ATTR_CONVERSATION_ID: _get_conversation_id(activity),
            constants.ATTR_IS_AGENTIC_REQUEST: activity.is_agentic_request(),
        })
        yield

@contextmanager
def start_span_adapter_send_activities(activities: list[Activity]) -> Iterator[None]:
    """Context manager for recording adapter send_activities call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_SEND_ACTIVITIES) as span:
        span.set_attributes({
            constants.ATTR_ACTIVITY_COUNT: len(activities),
            constants.ATTR_CONVERSATION_ID: _get_conversation_id(activities[0]) if activities else constants.UNKNOWN,
        })
        yield

@contextmanager
def start_span_adapter_update_activity(activity: Activity) -> Iterator[None]:
    """Context manager for recording adapter update_activity call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_UPDATE_ACTIVITY) as span:
        span.set_attributes({
            constants.ATTR_ACTIVITY_ID: activity.id or constants.UNKNOWN,
            constants.ATTR_CONVERSATION_ID: _get_conversation_id(activity),
        })
        yield

@contextmanager
def start_span_adapter_delete_activity(activity: Activity) -> Iterator[None]:
    """Context manager for recording adapter delete_activity call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_DELETE_ACTIVITY) as span:
        span.set_attributes({
            constants.ATTR_ACTIVITY_ID: activity.id or constants.UNKNOWN,
            constants.ATTR_CONVERSATION_ID: _get_conversation_id(activity),
        })
        yield

@contextmanager
def start_span_adapter_continue_conversation(activity: Activity) -> Iterator[None]:
    """Context manager for recording adapter continue_conversation call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_CONTINUE_CONVERSATION) as span:
        span.set_attributes({
            constants.ATTR_CONVERSATION_ID: _get_conversation_id(activity),
            constants.ATTR_IS_AGENTIC_REQUEST: activity.is_agentic_request(),
        })
        yield

@contextmanager
def start_span_adapter_create_connector_client(
    *,
    service_url: str,
    scopes: list[list] | None,
    is_agentic_request: bool,
) -> Iterator[None]:
    """Context manager for recording adapter create_connector_client call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_CREATE_CONNECTOR_CLIENT) as span:
        span.set_attributes({
            constants.ATTR_SERVICE_URL: service_url,
            constants.ATTR_AUTH_SCOPES: _format_scopes(scopes),
            constants.ATTR_IS_AGENTIC_REQUEST: is_agentic_request
        })
        yield

#
# AgentApplication
#

@contextmanager
def start_span_app_on_turn(turn_context: TurnContextProtocol) -> Iterator[None]:
    """Context manager for recording an app on_turn call, including success/failure and duration"""

    activity = turn_context.activity

    def callback(span: Span, duration: float, error: Exception | None):
        if error is None:
            _metrics.turn_total.add(1)
            _metrics.turn_duration.record(duration, {
                "conversation.id": activity.conversation.id if activity.conversation else "unknown",
                "channel.id": str(activity.channel_id),
            })
        else:
            _metrics.turn_errors.add(1)

    with agents_telemetry.start_timed_span(
        constants.SPAN_APP_ON_TURN,
        turn_context=turn_context,
        callback=callback,
    ) as span:
        span.set_attributes({
            constants.ATTR_ACTIVITY_TYPE: activity.type,
            constants.ATTR_ACTIVITY_ID: activity.id or constants.UNKNOWN,
        })
        yield

@contextmanager
def start_span_app_route_handler(turn_context: TurnContextProtocol) -> Iterator[None]:
    """Context manager for recording the app route handler span"""
    with agents_telemetry.start_as_current_span(constants.SPAN_APP_ROUTE_HANDLER, turn_context):
        yield

@contextmanager
def start_span_app_before_turn(turn_context: TurnContextProtocol) -> Iterator[None]:
    """Context manager for recording the app before turn span"""
    with agents_telemetry.start_as_current_span(constants.SPAN_APP_BEFORE_TURN, turn_context):
        yield

@contextmanager
def start_span_app_after_turn(turn_context: TurnContextProtocol) -> Iterator[None]:
    """Context manager for recording the app after turn span"""
    with agents_telemetry.start_as_current_span(constants.SPAN_APP_AFTER_TURN, turn_context):
        yield
    
@contextmanager
def start_span_app_download_files(turn_context: TurnContextProtocol) -> Iterator[None]:
    """Context manager for recording the app download files span"""
    with agents_telemetry.start_as_current_span(constants.SPAN_APP_DOWNLOAD_FILES, turn_context):
        yield

#
# ConnectorClient
#

@contextmanager
def _start_span_connector_op(
    span_name: str,
    *,
    conversation_id: str | None = None,
    activity_id: str | None = None,
) -> Iterator[Span]:

    def callback(span: Span, duration: int, error: Exception | None):
        _metrics.connector_request_total.add(1)
        _metrics.connector_request_duration.record(duration)

    with agents_telemetry.start_timed_span(
        span_name,
        callback=callback
    ) as span:
        if activity_id: span.set_attribute(constants.ATTR_ACTIVITY_ID, activity_id)
        if conversation_id: span.set_attribute(constants.ATTR_CONVERSATION_ID, conversation_id)
        yield span

@contextmanager
def start_span_connector_reply_to_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_op(
        constants.SPAN_CONNECTOR_REPLY_TO_ACTIVITY,
        conversation_id=conversation_id,
        activity_id=activity_id
    ):
        yield

@contextmanager
def start_span_connector_send_to_conversation(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_op(
        constants.SPAN_CONNECTOR_SEND_TO_CONVERSATION,
        conversation_id=conversation_id,
        activity_id=activity_id
    ):
        yield

@contextmanager
def start_span_connector_update_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_op(
        constants.SPAN_CONNECTOR_UPDATE_ACTIVITY,
        conversation_id=conversation_id,
        activity_id=activity_id
    ):
        yield

@contextmanager
def start_span_connector_delete_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_op(
        constants.SPAN_CONNECTOR_DELETE_ACTIVITY,
        conversation_id=conversation_id,
        activity_id=activity_id
    ):
        yield

@contextmanager
def start_span_connector_create_conversation() -> Iterator[None]:
    with _start_span_connector_op(constants.SPAN_CONNECTOR_CREATE_CONVERSATION):
        yield

@contextmanager
def start_span_connector_get_conversations() -> Iterator[None]:
    with _start_span_connector_op(constants.SPAN_CONNECTOR_GET_CONVERSATIONS):
        yield


@contextmanager
def start_span_connector_get_conversation_members() -> Iterator[None]:
    with _start_span_connector_op(constants.SPAN_CONNECTOR_GET_CONVERSATION_MEMBERS):
        yield


@contextmanager
def start_span_connector_upload_attachment(conversation_id: str) -> Iterator[None]:
    with _start_span_connector_op(
        constants.SPAN_CONNECTOR_UPDLOAD_ATTACHMENT,
        conversation_id=conversation_id    
    ):
        yield


@contextmanager
def start_span_connector_get_attachment(attachment_id: str) -> Iterator[None]:
    with _start_span_connector_op(constants.SPAN_CONNECTOR_GET_ATTACHMENT) as span:
        span.set_attribute(constants.ATTR_ATTACHMENT_ID, attachment_id)
        yield

#
# Storage
#


@contextmanager
def _start_span_storage_op(span_name: str, num_keys: int) -> Iterator[None]:

    def callback(span: Span, duration: int, error: Exception | None):
        _metrics.storage_operation_total.add(1)
        _metrics.storage_operation_duration.record(duration)

    with agents_telemetry.start_timed_span(
        span_name,
        callback=callback
    ) as span:
        span.set_attribute(constants.ATTR_NUM_KEYS, num_keys)
        yield

@contextmanager
def start_span_storage_read(num_keys: int) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_READ, num_keys): yield

@contextmanager
def start_span_storage_write(num_keys: int) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_WRITE, num_keys): yield

@contextmanager
def start_span_storage_delete(num_keys: int) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_DELETE, num_keys): yield

#
# TurnContext
#

@contextmanager
def start_span_turn_context_send_activity(turn_context: TurnContextProtocol) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_SEND_ACTIVITY, turn_context):
        yield


@contextmanager
def start_span_turn_context_update_activity(turn_context: TurnContextProtocol) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_UPDATE_ACTIVITY, turn_context):
        yield


@contextmanager
def start_span_turn_context_delete_activity(turn_context: TurnContextProtocol) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_DELETE_ACTIVITY, turn_context):
        yield