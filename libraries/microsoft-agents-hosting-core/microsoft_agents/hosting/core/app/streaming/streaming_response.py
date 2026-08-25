# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import uuid
import asyncio
import logging
from typing import Optional, Callable, Literal, cast, TYPE_CHECKING

from microsoft_agents.activity import (
    Activity,
    AIEntity,
    EntityTypes,
    Attachment,
    Channels,
    ClientCitation,
    DeliveryModes,
    SensitivityUsageInfo,
    ClientCitationAppearance,
    StreamInfo,
)

from microsoft_agents.hosting.core.errors import error_resources

from .citation import Citation
from .citation_util import CitationUtil

if TYPE_CHECKING:
    from microsoft_agents.hosting.core.turn_context import TurnContext

logger = logging.getLogger(__name__)

_TEAMS_STREAM_TIMED_OUT = "Content stream finished due to exceeded streaming time."
_DEFAULT_STREAMING_TAKING_TOO_LONG_MESSAGE = (
    "The response is taking longer than expected. Please wait while we continue "
    "to generate the response."
)
_M365_COPILOT_CHANNEL_PREFIX = "msteams:copilot"
_M365_STREAMING_TIMEOUT = 105.0
_M365_WORKING_NOTICE_INTERVAL = 35.0


class StreamingResponse:
    """
    A helper class for streaming responses to the client.

    This class is used to send a series of updates to the client in a single response.
    The expected sequence of calls is:

    `queue_informative_update()`, `queue_text_chunk()`, `queue_text_chunk()`, ..., `end_stream()`.

    Once `end_stream()` is called, the stream is considered ended and no further updates can be sent.
    """

    def __init__(self, context: TurnContext):
        """
        Creates a new StreamingResponse instance.

        Args:
            context: Context for the current turn of conversation with the user.
        """
        self._context = context
        self._initialize_state()

        # Set defaults based on channel
        self._set_defaults(context)

    def _initialize_state(self) -> None:
        """
        Initializes (or resets) all mutable streaming state to its default values.
        Called from both __init__() and reset().
        """
        self._is_streaming_channel = False
        self._interval = 0.1
        self._sequence_number = 1
        self._stream_id: Optional[str] = None
        self._message = ""
        self._queue: list[Callable[[], Activity | None]] = []
        self._queue_sync: Optional[asyncio.Task] = None
        self._chunk_queued = False
        self._ended = False
        self._cancelled = False
        self._user_cancelled = False
        self._stream_timed_out = False
        self._stream_timeout_notification_sent = False
        self._last_informational_message_sent = ""
        self._keep_alive_task: Optional[asyncio.Task[None]] = None
        self._stream_timeout_task: Optional[asyncio.Task[None]] = None
        self._stream_timeout_recovery_complete: Optional[asyncio.Event] = None
        if not hasattr(self, "_streaming_taking_too_long_message"):
            self._streaming_taking_too_long_message = (
                _DEFAULT_STREAMING_TAKING_TOO_LONG_MESSAGE
            )
        self._attachments: Optional[list[Attachment]] = None
        self._citations: list[ClientCitation] = []
        self._sensitivity_label: Optional[SensitivityUsageInfo] = None
        self._enable_feedback_loop = False
        self._feedback_loop_type: Optional[Literal["default", "custom"]] = None
        self._enable_generated_by_ai_label = False

    def queue_informative_update(self, text: str) -> None:
        """
        Queues an informative update to be sent to the client.

        Informative updates do not contain the message content that the user will
        read but rather an indication that the agent is processing the request.

        Args:
            text: The informative text to send to the client.
        """
        if self._is_m365_copilot():
            self._last_informational_message_sent = text

        if self._cancelled or not self._is_streaming_channel or not text.strip():
            return

        if self._ended:
            raise RuntimeError(str(error_resources.StreamAlreadyEnded))

        # Queue a typing activity
        def create_activity():
            activity = Activity(
                type="typing",
                text=text,
                entities=[
                    StreamInfo(
                        stream_type="informative",
                        stream_sequence=self._sequence_number,
                    )
                ],
            )
            self._sequence_number += 1
            return activity

        self._queue_activity(create_activity)

    def queue_text_chunk(
        self, text: str, citations: Optional[list[Citation]] = None
    ) -> None:
        """
        Queues a chunk of partial message text to be sent to the client.

        The text will be sent as quickly as possible to the client.
        Chunks may be combined before delivery to the client.

        Args:
            text: Partial text of the message to send.
            citations: Citations to be included in the message.
        """
        if self._cancelled:
            return
        if self._ended:
            raise RuntimeError(str(error_resources.StreamAlreadyEnded))

        # Update full message text
        self._message += text

        # If there are citations, modify the content so that the sources are numbers instead of [doc1], [doc2], etc.
        self._message = CitationUtil.format_citations_response(self._message)

        # Queue the next chunk only while the channel accepts streaming updates.
        if self._is_streaming_channel:
            self._queue_next_chunk()

    async def end_stream(self) -> None:
        """
        Ends the stream by sending the final message to the client.
        """
        if self._ended:
            raise RuntimeError(str(error_resources.StreamAlreadyEnded))

        self._ended = True
        await self._wait_for_stream_timeout_recovery()
        self._clear_stream_timers()

        if self._cancelled:
            return

        if not self._is_streaming_channel:
            # A failed streaming send can still be updating the timed-out activity.
            # Wait so that the completed response is always the last activity.
            await self.wait_for_queue()

            if (
                self._stream_timeout_notification_sent
                and not self._message
                and not self._attachments
            ):
                return

            final_activity = self._create_final_message(include_stream_info=False)
            if self._should_update_final_activity():
                updated = await self._update_activity(final_activity)
                if not updated:
                    await self._send_activity(
                        final_activity,
                        ensure_stream_info=False,
                    )
            else:
                await self._send_activity(
                    final_activity,
                    ensure_stream_info=False,
                )
            return

        # Queue final message.
        self._queue_next_chunk()

        # Wait for the queue to drain
        await self.wait_for_queue()

        # The final streaming send can itself report a channel timeout. Its queued
        # activity was discarded and must be applied after timeout recovery.
        if self._should_update_final_activity():
            final_activity = self._create_final_message(include_stream_info=False)
            updated = await self._update_activity(final_activity)
            if not updated:
                await self._send_activity(
                    final_activity,
                    ensure_stream_info=False,
                )
        elif not self._is_streaming_channel:
            await self._send_activity(
                self._create_final_message(include_stream_info=False),
                ensure_stream_info=False,
            )

    @property
    def is_streaming_channel(self) -> bool:
        """Whether the current channel accepts streaming activities."""
        return self._is_streaming_channel

    @property
    def streaming_taking_too_long_message(self) -> str:
        """Message sent when streaming takes longer than the channel allows."""
        return self._streaming_taking_too_long_message

    @streaming_taking_too_long_message.setter
    def streaming_taking_too_long_message(self, message: str) -> None:
        self._streaming_taking_too_long_message = message

    async def send_stream_timed_out_notification(self, message: str) -> bool:
        """End streaming while allowing the underlying operation to continue."""
        if self._ended or self._cancelled or not self._is_streaming_channel:
            return False

        recovery_complete = self._begin_stream_timeout_recovery()
        try:
            # Stop accepting stream work before waiting. Otherwise, a producer can
            # keep adding activities faster than the queue drains and delay this
            # notification until after the channel timeout.
            self._is_streaming_channel = False
            self._queue.clear()
            self._chunk_queued = False
            self._clear_stream_timers()

            # Preserve ordering with the one activity that can already be in flight.
            await self.wait_for_queue()
            sent = await self._send_activity(
                self._create_stream_stopped_message(message)
            )
            if not sent:
                return False

            self._stream_timeout_notification_sent = True
            return True
        finally:
            self._complete_stream_timeout_recovery(recovery_complete)

    def set_attachments(self, attachments: list[Attachment]) -> None:
        """
        Sets the attachments to attach to the final chunk.

        Args:
            attachments: List of attachments.
        """
        self._attachments = attachments

    def add_attachment(self, attachment: Attachment) -> None:
        """
        Adds an attachment to the collection of attachments for the final message.

        Attachments are only included in the final message sent by `end_stream()`.
        They are not sent in intermediate typing activities.

        Args:
            attachment: The attachment to add. Must not be None.

        Raises:
            ValueError: If attachment is None.
        """
        if attachment is None:
            raise ValueError("attachment cannot be None")

        if self._attachments is None:
            self._attachments = []
        self._attachments.append(attachment)

    async def reset(self) -> None:
        """
        Resets the streaming response to its initial state.
        If the stream is still running, this will wait for completion.
        """
        await self.wait_for_queue()
        self._clear_stream_timers()
        self._initialize_state()

        # Set defaults based on channel
        self._set_defaults(self._context)

    def set_sensitivity_label(self, sensitivity_label: SensitivityUsageInfo) -> None:
        """
        Sets the sensitivity label to attach to the final chunk.

        Args:
            sensitivity_label: The sensitivity label.
        """
        self._sensitivity_label = sensitivity_label

    def set_citations(self, citations: list[Citation]) -> None:
        """
        Sets the citations for the full message.

        Args:
            citations: Citations to be included in the message.
        """
        if citations:
            if not self._citations:
                self._citations = []

            curr_pos = len(self._citations)

            for citation in citations:
                client_citation = ClientCitation(
                    position=curr_pos + 1,
                    appearance=ClientCitationAppearance(
                        name=citation.title or f"Document #{curr_pos + 1}",
                        abstract=CitationUtil.snippet(citation.content, 480),
                        url=citation.url,
                    ),
                )
                curr_pos += 1
                self._citations.append(client_citation)

    def set_feedback_loop(self, enable_feedback_loop: bool) -> None:
        """
        Sets the Feedback Loop in Teams that allows a user to
        give thumbs up or down to a response.
        Default is False.

        Args:
            enable_feedback_loop: If true, the feedback loop is enabled.
        """
        self._enable_feedback_loop = enable_feedback_loop

    def set_feedback_loop_type(
        self, feedback_loop_type: Literal["default", "custom"]
    ) -> None:
        """
        Sets the type of UI to use for the feedback loop.

        Args:
            feedback_loop_type: The type of the feedback loop.
        """
        self._feedback_loop_type = feedback_loop_type

    def set_generated_by_ai_label(self, enable_generated_by_ai_label: bool) -> None:
        """
        Sets the Generated by AI label in Teams.
        Default is False.

        Args:
            enable_generated_by_ai_label: If true, the label is added.
        """
        self._enable_generated_by_ai_label = enable_generated_by_ai_label

    def get_message(self) -> str:
        """
        Returns the most recently streamed message.
        """
        return self._message

    async def wait_for_queue(self) -> None:
        """
        Waits for the outgoing activity queue to be empty.
        """
        if self._queue_sync:
            await self._queue_sync

    def _set_defaults(self, context: TurnContext):

        channel = (
            context.activity.channel_id.channel if context.activity.channel_id else None
        )

        if context.activity.delivery_mode == DeliveryModes.expect_replies:
            # Replies are buffered until the turn completes. Running streaming
            # timers here produces late, misleading timeout activities.
            self._is_streaming_channel = False
        elif channel == Channels.ms_teams:
            if context.activity.is_agentic_request():
                # Agentic requests do not support streaming responses at this time.
                # TODO : Enable streaming for agentic requests when supported.
                self._is_streaming_channel = False
            else:
                self._is_streaming_channel = True
                self._interval = 1.0
        elif channel in [Channels.webchat, Channels.direct_line]:
            self._is_streaming_channel = True
            self._interval = 0.5
            self._stream_id = str(uuid.uuid4())
        elif context.activity.delivery_mode == DeliveryModes.stream:
            self._is_streaming_channel = True
            self._interval = 0.1
            self._stream_id = str(uuid.uuid4())
        else:
            self._is_streaming_channel = False

    def _queue_next_chunk(self) -> None:
        """
        Queues the next chunk of text to be sent to the client.
        """
        # Are we already waiting to send a chunk?
        if self._chunk_queued:
            return

        # Queue a chunk of text to be sent
        self._chunk_queued = True

        def create_activity() -> Activity | None:
            self._chunk_queued = False
            if self._ended:
                activity = self._create_final_message(include_stream_info=True)
            elif self._is_streaming_channel:
                # Send typing activity
                activity = Activity(
                    type="typing",
                    text=self._message,
                    entities=[
                        StreamInfo(
                            stream_type="streaming",
                            stream_sequence=self._sequence_number,
                        )
                    ],
                )
            else:
                return
            if not self._ended:
                self._sequence_number += 1
            return activity

        self._queue_activity(create_activity)

    def _queue_activity(self, factory: Callable[[], Activity | None]) -> None:
        """
        Queues an activity to be sent to the client.
        """
        self._queue.append(factory)

        # If there's no sync in progress, start one
        if not self._queue_sync:
            self._queue_sync = asyncio.create_task(self._drain_queue())

    async def _drain_queue(self) -> None:
        """
        Sends any queued activities to the client until the queue is empty.
        """
        try:
            logger.debug(f"Draining queue with {len(self._queue)} activities.")
            while self._queue:
                factory = self._queue.pop(0)
                activity = factory()
                if activity:
                    await self._send_activity(activity)
        except Exception as err:
            logger.error(
                "Error occurred when draining the streaming activity queue: %s",
                type(err).__name__,
            )
            raise
        finally:
            self._queue_sync = None

    def _create_final_message(self, *, include_stream_info: bool) -> Activity:
        entities = []
        if include_stream_info:
            entities.append(
                StreamInfo(
                    stream_type="final",
                )
            )

        activity = Activity(
            type="message",
            text=self._message or "end stream response",
            attachments=self._attachments or [],
            entities=entities,
        )
        if self._should_update_final_activity() and self._stream_id:
            activity.id = self._stream_id
        return activity

    def _create_stream_stopped_message(self, message: str) -> Activity:
        notification = message or "No text was streamed"
        text = f"{self._message}\n\n{notification}" if self._message else notification
        activity = Activity(
            type="message",
            text=text,
            entities=[
                StreamInfo(
                    stream_type="final",
                    stream_result="success" if self._message else "error",
                )
            ],
        )
        return activity

    def _create_stream_timed_out_message(
        self, *, add_stream_final: bool = False
    ) -> Activity:
        text = (
            f"{self._message}\n\n{self.streaming_taking_too_long_message}\n"
            if self._message
            else self.streaming_taking_too_long_message
        )
        entities = []
        if add_stream_final:
            stream_info = StreamInfo(
                stream_type="final",
                stream_result="success" if self._message else "error",
            )
            if self._stream_id:
                stream_info.stream_id = self._stream_id
            entities.append(stream_info)

        return Activity(
            id=self._stream_id,
            type="message",
            text=text,
            entities=entities,
        )

    def _create_stream_timed_out_streaming_update(self) -> Activity:
        text = (
            f"{self._message}\n\n{self.streaming_taking_too_long_message}\n"
            if self._message
            else self.streaming_taking_too_long_message
        )
        activity = Activity(
            type="typing",
            text=text,
            entities=[
                StreamInfo(
                    stream_type="streaming",
                    stream_sequence=self._sequence_number,
                )
            ],
        )
        self._sequence_number += 1
        return activity

    async def _send_activity(
        self, activity: Activity, *, ensure_stream_info: bool = True
    ) -> bool:
        """
        Sends an activity to the client and saves the stream ID returned.

        Args:
            activity: The activity to send.
        """

        self._start_stream_timers()

        streaminfo_entity: StreamInfo | None = None

        if not activity.entities and ensure_stream_info:
            streaminfo_entity = StreamInfo(stream_sequence=self._sequence_number)
            self._sequence_number += 1
            activity.entities = [streaminfo_entity]
        elif activity.entities:
            for entity in activity.entities:
                if entity.type == EntityTypes.STREAM_INFO:
                    streaminfo_entity = cast(StreamInfo, entity)
                    break

            if not streaminfo_entity and ensure_stream_info:
                # If no streaminfo entity exists, create one
                streaminfo_entity = StreamInfo(stream_sequence=self._sequence_number)
                self._sequence_number += 1
                activity.entities.append(streaminfo_entity)

        # Set activity ID to the assigned stream ID
        if self._stream_id and streaminfo_entity:
            activity.id = self._stream_id
            streaminfo_entity.stream_id = self._stream_id

        # the activity.add_ai_metadata call further down will add citations.
        # The extra condition here is to avoid duplication
        if (
            self._citations
            and not self._ended
            and not self._enable_generated_by_ai_label
        ):
            # Filter out the citations unused in content.
            curr_citations = CitationUtil.get_used_citations(
                self._message, self._citations
            )
            if curr_citations:
                activity.entities.append(
                    AIEntity(
                        type="https://schema.org/Message",
                        id="",
                        citation=curr_citations,
                    )
                )

        # Add in Powered by AI feature flags
        if self._ended:
            if self._enable_feedback_loop and self._feedback_loop_type:
                # Add feedback loop to streaminfo entity
                if streaminfo_entity:
                    streaminfo_entity.feedback_loop = {"type": self._feedback_loop_type}
            else:
                # Add feedback loop enabled to streaminfo entity
                if streaminfo_entity:
                    streaminfo_entity.feedback_loop_enabled = self._enable_feedback_loop
        # Add in Generated by AI
        if self._enable_generated_by_ai_label:
            curr_citations = CitationUtil.get_used_citations(
                self._message, self._citations
            )
            activity.add_ai_metadata(curr_citations, self._sensitivity_label)

        try:
            response = await self._context.send_activity(activity)

            if not self._stream_id and response:
                self._stream_id = response.id

            if (
                self._is_m365_copilot()
                and self._is_streaming_channel
                and not self._ended
            ):
                self._schedule_keep_alive()

            await asyncio.sleep(self._interval)
            return True
        except Exception as err:  # pylint: disable=broad-exception-caught
            await self._handle_send_error(err)
            return False

    async def _handle_send_error(self, err: Exception) -> None:
        message = str(err)
        normalized_message = message.lower()
        is_content_not_allowed = "contentstreamnotallowed" in normalized_message
        is_teams_403 = "403" in normalized_message and self._is_teams_channel()
        is_timeout = _TEAMS_STREAM_TIMED_OUT.lower() in normalized_message
        is_streaming_unsupported = (
            "badargument" in normalized_message
            and "streaming api is not enabled" in normalized_message
        )

        if not (is_content_not_allowed or is_teams_403 or is_streaming_unsupported):
            logger.error(
                "Exception during StreamingResponse send_activity: %s",
                type(err).__name__,
            )
            raise err

        self._cancelled = True
        self._queue.clear()
        self._chunk_queued = False
        self._clear_stream_timers()

        if (is_content_not_allowed or is_teams_403) and is_timeout:
            logger.warning(
                "Client stopped streaming because the allowed time was exceeded: %s",
                message,
            )
            self._stream_timed_out = True
            self._cancelled = False
            self._is_streaming_channel = False
            if not self._is_m365_copilot():
                await self._update_activity(self._create_stream_timed_out_message())
        elif is_content_not_allowed or is_teams_403:
            logger.warning("Streaming content was cancelled by the client: %s", message)
            self._user_cancelled = True
        else:
            logger.warning(
                "The interaction does not support streaming. Using non-streaming mode."
            )
            self._cancelled = False
            self._is_streaming_channel = False

    async def _update_activity(self, activity: Activity) -> bool:
        try:
            await self._context.update_activity(activity)
            return True
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Exception during StreamingResponse update_activity: %s",
                type(err).__name__,
            )
            return False

    def _start_stream_timers(self) -> None:
        if (
            not self._is_m365_copilot()
            or not self._is_streaming_channel
            or self._ended
            or self._stream_timeout_task is not None
        ):
            return

        self._schedule_keep_alive()
        self._stream_timeout_task = asyncio.create_task(self._run_stream_timeout())

    def _schedule_keep_alive(self) -> None:
        if not self._is_m365_copilot() or not self._is_streaming_channel or self._ended:
            return

        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
        self._keep_alive_task = asyncio.create_task(self._run_keep_alive())

    async def _run_keep_alive(self) -> None:
        try:
            await asyncio.sleep(_M365_WORKING_NOTICE_INTERVAL)
            self._keep_alive_task = None
            if not self._ended and self._is_streaming_channel and not self._queue:
                if self._message:
                    # Informative updates no longer affect the client after text
                    # streaming starts. Resend the cumulative text as a streaming
                    # update to keep the M365 Copilot stream active.
                    self._queue_next_chunk()
                else:
                    self.queue_informative_update(
                        self._last_informational_message_sent.strip()
                        and self._last_informational_message_sent
                        or self.streaming_taking_too_long_message
                    )
        except asyncio.CancelledError:
            return

    async def _run_stream_timeout(self) -> None:
        try:
            await asyncio.sleep(_M365_STREAMING_TIMEOUT)
            await self._handle_m365_stream_timeout()
        except asyncio.CancelledError:
            return
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error handling the M365 Copilot streaming timeout: %s",
                type(err).__name__,
            )
        finally:
            if self._stream_timeout_task is asyncio.current_task():
                self._stream_timeout_task = None

    async def _handle_m365_stream_timeout(self) -> None:
        if (
            self._ended
            or self._cancelled
            or not self._is_streaming_channel
            or not self._is_m365_copilot()
        ):
            return

        recovery_complete = self._begin_stream_timeout_recovery()
        try:
            logger.warning(
                "M365 Copilot streaming reached its maximum duration. "
                "Continuing in non-streaming mode."
            )

            timed_out_activities = []
            if self._message:
                timed_out_activities.append(
                    self._create_stream_timed_out_streaming_update()
                )
            timed_out_activities.append(
                self._create_stream_timed_out_message(add_stream_final=True)
            )

            self._is_streaming_channel = False
            self._queue.clear()
            self._chunk_queued = False
            self._clear_stream_timers()

            # Preserve ordering with an activity that may already be in flight, then
            # track whether the final stream terminator was actually delivered.
            await self.wait_for_queue()
            for timed_out_activity in timed_out_activities[:-1]:
                await self._send_activity(timed_out_activity)
            self._stream_timeout_notification_sent = await self._send_activity(
                timed_out_activities[-1]
            )
        finally:
            self._complete_stream_timeout_recovery(recovery_complete)

    def _begin_stream_timeout_recovery(self) -> asyncio.Event:
        recovery_complete = asyncio.Event()
        self._stream_timeout_recovery_complete = recovery_complete
        return recovery_complete

    def _complete_stream_timeout_recovery(
        self, recovery_complete: asyncio.Event
    ) -> None:
        recovery_complete.set()
        if self._stream_timeout_recovery_complete is recovery_complete:
            self._stream_timeout_recovery_complete = None

    async def _wait_for_stream_timeout_recovery(self) -> None:
        recovery_complete = self._stream_timeout_recovery_complete
        if recovery_complete:
            await recovery_complete.wait()

    def _clear_stream_timers(self) -> None:
        current_task = asyncio.current_task()
        for task_name in ("_keep_alive_task", "_stream_timeout_task"):
            task = getattr(self, task_name, None)
            setattr(self, task_name, None)
            if task and task is not current_task and not task.done():
                task.cancel()

    def _is_m365_copilot(self) -> bool:
        channel_id = self._context.activity.channel_id
        if not channel_id:
            return False

        normalized_channel_id = str(channel_id).lower()
        return normalized_channel_id == _M365_COPILOT_CHANNEL_PREFIX or (
            normalized_channel_id.startswith(f"{_M365_COPILOT_CHANNEL_PREFIX}-")
            or normalized_channel_id.startswith(f"{_M365_COPILOT_CHANNEL_PREFIX}:")
        )

    def _is_teams_channel(self) -> bool:
        channel_id = self._context.activity.channel_id
        return bool(channel_id) and channel_id.channel == Channels.ms_teams

    def _should_update_final_activity(self) -> bool:
        if self._is_m365_copilot():
            return False
        return self._stream_timed_out or (
            self._stream_timeout_notification_sent and self._is_teams_channel()
        )
