# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
import uuid
from typing import List, Optional, Callable, Literal, TYPE_CHECKING
from dataclasses import dataclass

from microsoft.agents.core.models import (
    Activity,
    Entity,
    Attachment,
    ClientCitation,
    SensitivityUsageInfo,
    add_ai_to_activity,
    Channels,
    DeliveryModes,
)

if TYPE_CHECKING:
    from microsoft.agents.builder.turn_context import TurnContext

from .citation import Citation
from .citation_util import CitationUtil

logger = logging.getLogger(__name__)


@dataclass
class StreamingChannelData:
    """
    Structure of the outgoing channelData field for streaming responses.

    The expected sequence of streamTypes is:
    'informative', 'streaming', 'streaming', ..., 'final'.

    Once a 'final' message is sent, the stream is considered ended.
    """

    stream_type: Literal["informative", "streaming", "final"]
    """The type of message being sent."""

    stream_sequence: int
    """Sequence number of the message in the stream. Starts at 1 for the first message."""

    stream_id: Optional[str] = None
    """ID of the stream. Assigned after the initial update is sent."""


class StreamingResponse:
    """
    A helper class for streaming responses to the client.

    This class is used to send a series of updates to the client in a single response.
    The expected sequence of calls is:

    `queue_informative_update()`, `queue_text_chunk()`, `queue_text_chunk()`, ..., `end_stream()`.    Once `end_stream()` is called, the stream is considered ended and no further updates can be sent.
    """

    def __init__(self, context: "TurnContext"):
        """
        Creates a new StreamingResponse instance.

        Args:
            context: Context for the current turn of conversation with the user.
        """
        self._context = context
        self._next_sequence = 1
        self._stream_id: Optional[str] = None
        self._message = ""
        self._attachments: Optional[List[Attachment]] = None
        self._ended = False
        self._cancelled = False
        self._informative_sent = False
        self._message_updated = False
        self._final_message = None

        # Queue for outgoing activities
        self._queue: List[Callable[[], Activity]] = []
        self._queue_sync: Optional[asyncio.Task] = None
        self._chunk_queued = False
        self._timer_task: Optional[asyncio.Task] = None

        # Powered by AI feature flags
        self._enable_feedback_loop = False
        self._feedback_loop_type: Optional[Literal["default", "custom"]] = None
        self._enable_generated_by_ai_label = False
        self._citations: Optional[List[ClientCitation]] = []
        self._sensitivity_label: Optional[SensitivityUsageInfo] = None

        # Channel-specific settings
        self._is_teams_channel = False
        self._interval = 100  # Default interval in milliseconds
        self._is_streaming_channel = False

        # Initialize channel-specific settings
        self._set_defaults(context)

    @property
    def stream_id(self) -> Optional[str]:
        """
        Gets the stream ID of the current response.
        Assigned after the initial update is sent.
        """
        return self._stream_id

    @property
    def citations(self) -> Optional[List[ClientCitation]]:
        """Gets the citations of the current response."""
        return self._citations

    @property
    def updates_sent(self) -> int:
        """Gets the number of updates sent for the stream."""
        return self._next_sequence - 1

    @property
    def final_message(self) -> Optional[Activity]:
        """
        Gets the final message that will be sent to the client.
        This is only set after `end_stream()` is called.
        """
        return self._final_message

    @final_message.setter
    def set_final_message(self, value: Activity) -> None:
        """Sets the final message to be sent to the client.

        Args:
            value: The final message to send.
        """
        self._final_message = value

    def queue_informative_update(self, text: str) -> None:
        """
        Queues an informative update to be sent to the client.

        Args:
            text: Text of the update to send.
        """
        if not self._is_streaming_channel:
            return

        if self._ended:
            raise RuntimeError("The stream has already ended.")

        self._informative_sent = True

        # Queue a typing activity
        def create_activity():
            activity = Activity(
                type="typing",
                text=text,
                channel_data={
                    "streamType": "informative",
                    "streamSequence": self._next_sequence,
                },
            )
            self._next_sequence += 1
            return activity

        self._queue_activity(create_activity)

    def queue_text_chunk(
        self, text: str, citations: Optional[List[Citation]] = None
    ) -> None:
        """
        Queues a chunk of partial message text to be sent to the client.

        The text will be sent as quickly as possible to the client.
        Chunks may be combined before delivery to the client.

        Args:
            text: Partial text of the message to send.
            citations: Citations to be included in the message.
        """
        if not text or self._cancelled:
            return

        if self._ended:
            raise RuntimeError("The stream has already ended.")

        if not self._informative_sent and self._is_teams_channel:
            raise RuntimeError(
                "Teams requires calling queue_informative_update() before queue_text_chunk()"
            )

        # Update full message text
        self._message += text

        # If there are citations, modify the content so that the sources are numbers instead of [doc1], [doc2], etc.
        self._message = CitationUtil.format_citations_response(self._message)

        self._message_updated = True

        # Start stream if we're on a streaming channel
        if self._is_streaming_channel:
            self._start_stream()

        # Queue the next chunk
        self._queue_next_chunk()

    async def end_stream(self) -> None:
        """
        Ends the stream by sending the final message to the client.
        """
        if not self._is_streaming_channel:
            if self._ended:
                raise RuntimeError("The stream has already ended.")

            self._ended = True

            # Timer isn't running for non-streaming channels. Just send the Message buffer as a message.
            if self.updates_sent > 0 or self._message or self._final_message:
                await self._send_final_message()
            return

        if self._ended:
            return

        self._ended = True

        if self.updates_sent == 0 or self._cancelled:
            # Nothing was queued. Nothing to "end".
            return

        # Stop the streaming timer
        self._stop_stream()

        # Wait for the queue to drain and send final message
        await self.wait_for_queue()

        # TODO: NEED to revisit final message logic
        # if self.updates_sent > 0 or self._final_message:
        # await self._send_final_message()

    def set_attachments(self, attachments: List[Attachment]) -> None:
        """
        Sets the attachments to attach to the final chunk.

        Args:
            attachments: List of attachments.
        """
        self._attachments = attachments

    def set_sensitivity_label(self, sensitivity_label: SensitivityUsageInfo) -> None:
        """
        Sets the sensitivity label to attach to the final chunk.

        Args:
            sensitivity_label: The sensitivity label.
        """
        self._sensitivity_label = sensitivity_label

    def set_citations(self, citations: List[Citation]) -> None:
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
                    type="Claim",
                    position=curr_pos + 1,
                    appearance={
                        "type": "DigitalDocument",
                        "name": citation.title or f"Document #{curr_pos + 1}",
                        "abstract": CitationUtil.snippet(citation.content, 477),
                    },
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

    def _queue_next_chunk(self) -> None:
        """
        Queues the next chunk of text to be sent to the client.
        """
        # Are we already waiting to send a chunk?
        if self._chunk_queued:
            return

        # Queue a chunk of text to be sent
        self._chunk_queued = True

        def create_activity():
            self._chunk_queued = False
            if self._ended:
                # Send final message
                activity = Activity(
                    type="message",
                    text=self._message or "end stream response",
                    attachments=self._attachments or [],
                    channel_data={
                        "streamType": "final",
                        "streamSequence": self._next_sequence,
                    },
                )
            else:
                # Send typing activity
                activity = Activity(
                    type="typing",
                    text=self._message,
                    channel_data={
                        "streamType": "streaming",
                        "streamSequence": self._next_sequence,
                    },
                )
            self._next_sequence += 1
            return activity

        self._queue_activity(create_activity)

    def _queue_activity(self, factory: Callable[[], Activity]) -> None:
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
                await self._send_activity(activity)
        except Exception as err:
            logger.error(f"Error occurred when sending activity while streaming: {err}")
            raise
        finally:
            self._queue_sync = None

    async def _send_activity(self, activity: Activity) -> None:
        """
        Sends an activity to the client and saves the stream ID returned.

        Args:
            activity: The activity to send.
        """
        # Set activity ID to the assigned stream ID
        if self._stream_id:
            activity.id = self._stream_id
            if not activity.channel_data:
                activity.channel_data = {}
            activity.channel_data["streamId"] = self._stream_id

        if not activity.entities:
            activity.entities = []

        activity.entities.append(Entity(type="streaminfo", **activity.channel_data))

        if self._citations and len(self._citations) > 0 and not self._ended:
            # Filter out the citations unused in content.
            curr_citations = CitationUtil.get_used_citations(
                self._message, self._citations
            )
            if curr_citations:
                activity.entities.append(
                    Entity(
                        type="https://schema.org/Message",
                        schema_type="Message",
                        context="https://schema.org",
                        id="",
                        citation=curr_citations,
                    )
                )

        # Add in Powered by AI feature flags
        if self._ended:
            # TODO: fix feedback loop
            if self._enable_feedback_loop and self._feedback_loop_type:
                if not activity.channel_data:
                    activity.channel_data = {}
                activity.channel_data["feedbackLoop"] = {
                    "type": self._feedback_loop_type
                }
            else:
                if not activity.channel_data:
                    activity.channel_data = {}
                activity.channel_data["feedbackLoopEnabled"] = (
                    self._enable_feedback_loop
                )

        # Add in Generated by AI
        if self._enable_generated_by_ai_label:
            add_ai_to_activity(activity, self._citations, self._sensitivity_label)

        if self._is_teams_channel:
            activity.channel_data = None

        # Send activity
        response = await self._context.send_activity(activity)

        # Save assigned stream ID
        if not self._stream_id and response:
            self._stream_id = response.id

    @property
    def is_streaming_channel(self) -> bool:
        """
        Indicate if the current channel supports intermediate messages.

        Channels that don't support intermediate messages will buffer
        text, and send a normal final message when end_stream is called.
        """
        return self._is_streaming_channel

    @property
    def interval(self) -> int:
        """
        The interval in milliseconds at which intermediate messages are sent.

        Teams default: 1000
        WebChat default: 500
        Other channels: 100
        """
        return self._interval

    @interval.setter
    def interval(self, value: int) -> None:
        """Set the interval for sending intermediate messages."""
        self._interval = value

    def is_stream_started(self) -> bool:
        """Check if the streaming timer has been started."""
        return self._timer_task is not None and not self._timer_task.done()

    def _set_defaults(self, context: "TurnContext") -> None:
        """Set channel-specific defaults based on the turn context."""
        channel_id = getattr(context.activity, "channel_id", None)
        delivery_mode = getattr(context.activity, "delivery_mode", None)

        self._is_teams_channel = channel_id == Channels.ms_teams

        if self._is_teams_channel:
            # Teams MUST use the Activity.Id returned from the first Informative message for
            # subsequent intermediate messages. Do not set StreamId here.
            self._interval = 1000
            self._is_streaming_channel = True
        elif channel_id == Channels.webchat:
            self._interval = 500
            self._is_streaming_channel = True
            # WebChat will use whatever StreamId is created
            self._stream_id = str(uuid.uuid4())
        else:
            # Support streaming for DeliveryMode.Stream
            self._is_streaming_channel = delivery_mode == DeliveryModes.stream
            self._interval = 100

    def _start_stream(self) -> None:
        """Start the streaming timer if not already started."""
        if self._timer_task is None and self._is_streaming_channel:
            self._timer_task = asyncio.create_task(self._send_intermediate_messages())

    def _stop_stream(self) -> None:
        """Stop the streaming timer."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            self._timer_task = None

    async def _send_intermediate_messages(self) -> None:
        """Timer task to send intermediate messages at intervals."""
        try:
            while not self._ended and not self._cancelled:
                await asyncio.sleep(self._interval / 1000.0)  # Convert ms to seconds

                if self._message_updated:
                    self._queue_next_chunk()
                    self._message_updated = False

                # Process any queued activities
                await self._drain_queue()

        except asyncio.CancelledError:
            pass

    async def _send_final_message(self) -> None:
        """Send the final message with all accumulated content."""
        activity = self.final_message or Activity(
            type="message",
            text=self._message or "No text was streamed",
            attachments=self._attachments,
            entities=[],
        )

        if self._is_streaming_channel:
            channel_data = {
                "streamType": "final",
                # "streamSequence": self._next_sequence,
                "streamResult": "success" if self._message else "error",
                "streamId": self._stream_id,
            }

            activity.entities.append(Entity(type="streaminfo", **channel_data))

            if not self._is_teams_channel:
                activity.channel_data = channel_data

            self._next_sequence += 1

        # Add AI entity if enabled
        if self._enable_generated_by_ai_label:
            used_citations = None
            if self._citations:
                used_citations = CitationUtil.get_used_citations(
                    self._message, self._citations
                )
            add_ai_to_activity(activity, used_citations, self._sensitivity_label)

        # Send the final activity
        await self._context.send_activity(activity)
