from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry.trace import Span

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core.turn_context import TurnContext

from . import _metrics, constants
from ._agents_telemetry import agents_telemetry

#
# Adapter
#

def _get_conversation_id(activity: Activity) -> str:
    return activity.conversation.id if activity.conversation else "unknown"

@contextmanager
def start_span_adapter_process(activity: Activity) -> Iterator[None]:
    """Context manager for recording adapter process call"""
    with agents_telemetry.start_as_current_span(constants.SPAN_ADAPTER_PROCESS) as span:
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

#
# AgentApplication
#

@contextmanager
def start_span_app_on_turn(turn_context: TurnContextProtocolProtocol) -> Iterator[None]:
    """Context manager for recording an app on_turn call, including success/failure and duration"""

    activity = turn_context.activity

    def callback(span: Span, duration: float, error: Exception | None):
        if error is None:
            _metrics.TURN_TOTAL.add(1)
            _metrics.TURN_DURATION.record(duration, {
                "conversation.id": activity.conversation.id if activity.conversation else "unknown",
                "channel.id": str(activity.channel_id),
            })
        else:
            _metrics.TURN_ERRORS.add(1)

    with agents_telemetry.start_timed_span(
        constants.SPAN_APP_RUN,
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
def _start_span_connector_activity_op(span_name: str, conversation_id: str, activity_id: str) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(span_name) as span:
        span.set_attribute(constants.ATTR_ACTIVITY_ID, activity_id)
        span.set_attribute(constants.ATTR_CONVERSATION_ID, conversation_id)
        yield

@contextmanager
def start_span_connector_reply_to_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_activity_op(constants.SPAN_CONNECTOR_REPLY_TO_ACTIVITY, conversation_id, activity_id):
        yield

@contextmanager
def start_span_connector_send_to_conversation(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_activity_op(constants.SPAN_CONNECTOR_SEND_TO_CONVERSATION, conversation_id, activity_id):
        yield

@contextmanager
def start_span_connector_update_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_activity_op(constants.SPAN_CONNECTOR_UPDATE_ACTIVITY, conversation_id, activity_id):
        yield

@contextmanager
def start_span_connector_delete_activity(conversation_id: str, activity_id: str) -> Iterator[None]:
    with _start_span_connector_activity_op(constants.SPAN_CONNECTOR_DELETE_ACTIVITY, conversation_id, activity_id):
        yield

@contextmanager
def start_span_connector_create_conversation() -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_CONNECTOR_CREATE_CONVERSATION):
        yield

@contextmanager
def start_span_connector_get_conversations() -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_CONNECTOR_GET_CONVERSATIONS):
        yield


@contextmanager
def start_span_connector_get_conversation_members() -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_CONNECTOR_GET_CONVERSATION_MEMBERS):
        yield


@contextmanager
def start_span_connector_upload_attachment(conversation_id: str) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_CONNECTOR_UPDLOAD_ATTACHMENT) as span:
        span.set_attribute(constants.ATTR_CONVERSATION_ID, conversation_id)
        yield


@contextmanager
def start_span_connector_get_attachment(attachment_id: str) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_CONNECTOR_GET_ATTACHMENT) as span:
        span.set_attribute(constants.ATTR_ATTACHMENT_ID, attachment_id)
        yield

#
# Storage
#


@contextmanager
def _start_span_storage_op(span_name: str, num_keys: int) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(span_name) as span:
        span.set_attribute(constants.ATTR_NUM_KEYS, num_keys)
        yield

@contextmanager
def start_span_storage_read(num_keys: int) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_READ, num_keys): yield

@contextmanager
def start_span_storage_write(self) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_WRITE, num_keys): yield

@contextmanager
def start_span_storage_delete(self) -> Iterator[None]:
    with _start_span_storage_op(constants.SPAN_STORAGE_DELETE, num_keys): yield

#
# Auth
#

@contextmanager
def start_span_auth_get_access_token(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_ACCESS_TOKEN):
        yield


@contextmanager
def start_span_auth_acquire_token_on_behalf_of(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_ACQUIRE_TOKEN_ON_BEHALF_OF):
        yield


@contextmanager
def start_span_auth_get_agentic_instance_token(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_AGENTIC_INSTANCE_TOKEN):
        yield


@contextmanager
def start_span_auth_get_agentic_user_token(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_AGENTIC_USER_TOKEN):
        yield


@contextmanager
def start_span_agent_post_activity(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span("agents.agentClient.postActivity"):
        yield


@contextmanager
def start_span_turn_send_activity(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_SEND_ACTIVITY):
        yield


@contextmanager
def start_span_turn_send_activities(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_SEND_ACTIVITY):
        yield


@contextmanager
def start_span_turn_update_activity(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_UPDATE_ACTIVITY):
        yield


@contextmanager
def start_span_turn_delete_activity(self) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_TURN_DELETE_ACTIVITY):
        yield

# def start_span_agent_turn(turn_context: TurnContextProtocol) -> Iterator[Span]:
#     """Context manager for recording an agent turn, including success/failure and duration"""

#     def callback(span: Span, duration: float, error: Exception | None):
#         if error is None:
#             _metrics.TURN_TOTAL.add(1)
#             _metrics.TURN_DURATION.record(duration, {
#                 "conversation.id": turn_context.activity.conversation.id if turn_context.activity.conversation else "unknown",
#                 "channel.id": str(turn_context.activity.channel_id),
#             })
#         else:
#             self._turn_errors.add(1)

#     with self._start_timed_span(
#         constants.AGENT_TURN_OPERATION_NAME,
#         turn_context=turn_context,
#         callback=callback,
#     ) as span:
#         yield span  # execute the turn operation in the with block

# @contextmanager
# def start_span_app_run(turn_context: TurnContextProtocol) -> Iterator[Span]:
#     """Context manager for recording an app run, including success/failure and duration"""

#     with agents_telemetry.start_as_current_span(
#         constants.SPAN_APP_RUN,
#         turn_context=turn_context
#     )
#     with self._start_timed_span(
#         constants.APP_RUN_OPERATION_NAME,
#         callback=callback
#     ) as span:
#         span.set_attribute("app.name", app_name)
#         yield span  # execute the app run operation in the with block



# def start_span_adapter_process(self):
#     """Context manager for recording adapter processing operations"""

#     def callback(span: Span, duration: float, error: Exception | None):
#         if error is None:
#             self._adapter_process_duration.record(duration)

#     with self._start_timed_span(
#         constants.ADAPTER_PROCESS_OPERATION_NAME,
#         callback=callback
#     ) as span:
#         yield span  # execute the adapter processing in the with block

# def _start_span_adapter_activity_op(span_name: str, conversation_id: str | None = None):


#     @contextmanager
#     def _instrument_adapter_activity_op(span_name: str):
#         """Context manager for recording adapter activity operations ()"""
#         with self.start_as_current_span(span_name) as span:
#             yield span

#     @contextmanager
#     def instrument_adapter_send_activities(activity_count: int, conversation_id: str) -> None:
#         """Context manager for recording adapter SendActivities calls"""
#         with self._instrument_adapter_activity_op(constants.SPAN_ADAPTER_SEND_ACTIVITIES):
#             yield

#     @contextmanger
#     def instrument_adapter_update_activity(activity_id: str, conversation_id: str) -> None:
#         """Context manager for recording adapter UpdateActivity calls"""
#         with self._instrument_adapter_activity_op(constants.SPAN_ADAPTER_UPDATE_ACTIVITY):
#             yield
    
#     @contextmanager


#     @contextmanager
#     def instrument_storage_op(
#         
#         operation_type: str,
#         num_keys: int,
#     ):
#         """Context manager for recording storage operations"""

#         def callback(span: Span, duration: float, error: Exception | None):
#             if error is None:
#                 self._storage_operations.add(1, {"operation": operation_type})
#                 self._storage_operation_duration.record(duration, {"operation": operation_type})

#         with self._start_timed_span(
#             constants.STORAGE_OPERATION_NAME_FORMAT.format(operation_type=operation_type),
#             callback=callback
#         ) as span:
#             span.set_attribute(constants.ATTR_NUM_KEYS, num_keys)
#             yield span  # execute the storage operation in the with block

#     @contextmanager
#     def instrument_connector_op(operation_name: str):
#         """Context manager for recording connector requests"""

#         def callback(span: Span, duration: float, error: Exception | None):
#             if error is None:
#                 self._connector_request_total.add(1, {"operation": operation_name})
#                 self._connector_request_duration.record(duration, {"operation": operation_name})

#         with self._start_timed_span(
#             constants.CONNECTOR_REQUEST_OPERATION_NAME_FORMAT.format(operation_name=operation_name),
#             callback=callback
#         ) as span:
#             yield span  # execute the connector request in the with block

#     @contextmanager
#     def instrument_auth_token_request(
#         
#         scopes: list[str] | None = None,
#         agentic_user_id: str | None = None,
#         agentic_app_instance_id: str | None = None
#     ):
#         """Context manager for recording auth token retrieval operations"""

#         def callback(span: Span, duration: float, error: Exception | None):
#             if error is None:
#                 self._auth_token_request_total.add(1)
#                 self._auth_token_requests_duration.record(duration)

#         with self._start_timed_span(
#             constants.AUTH_TOKEN_REQUEST_OPERATION_NAME,
#             callback=callback
#         ) as span:

#             attributes = {
#                 constants.ATTR_AUTH_SCOPES: scopes,
#                 constants.ATTR_AGENTIC_USER_ID: agentic_user_id,
#                 constants.ATTR_AGENTIC_APP_INSTANCE_ID: agentic_app_instance_id,
#             }
#             _remove_nones(attributes)
            
#             span.set_attributes(attributes)

#             yield span  # execute the auth token retrieval operation in the with block