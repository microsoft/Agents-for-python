# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
from typing import List, Optional, Callable, Literal, TYPE_CHECKING
from dataclasses import dataclass

from microsoft.agents.activity import (
    Activity,
    Entity,
    Attachment,
    Channels,
    ClientCitation,
    DeliveryModes,
    SensitivityUsageInfo,
    add_ai_to_activity,
)

if TYPE_CHECKING:
    from microsoft.agents.hosting.core.turn_context import TurnContext

from .citation import Citation
from .citation_util import CitationUtil

logger = logging.getLogger(__name__)


class StreamingResponse:
    """
    A helper class for streaming responses to the client.

    This class is used to send a series of updates to the client in a single response.
    The expected sequence of calls is:

    `queue_informative_update()`, `queue_text_chunk()`, `queue_text_chunk()`, ..., `end_stream()`.

    Once `end_stream()` is called, the stream is considered ended and no further updates can be sent.
    """

    def __init__(self, context: "TurnContext"):
        """
        Creates a new StreamingResponse instance.

        Args:
            context: Context for the current turn of conversation with the user.
        """
        self._context = context
        self._sequence_number = 1
        self._stream_id: Optional[str] = None
        self._message = ""
        self._attachments: Optional[List[Attachment]] = None
        self._ended = False
        self._cancelled = False

        # Queue for outgoing activities
        self._queue: List[Callable[[], Activity]] = []
        self._queue_sync: Optional[asyncio.Task] = None
        self._chunk_queued = False

        # Powered by AI feature flags
        self._enable_feedback_loop = False
        self._feedback_loop_type: Optional[Literal["default", "custom"]] = None
        self._enable_generated_by_ai_label = False
        self._citations: Optional[List[ClientCitation]] = []
        self._sensitivity_label: Optional[SensitivityUsageInfo] = None

        # Channel information
        self._is_streaming_channel: bool = False
        self._channel_id: Channels = None
        self._interval: float = 0.1  # Default interval for sending updates
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
        return self._sequence_number - 1

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

        # Queue a typing activity
        def create_activity():
            activity = Activity(
                type="typing",
                text=text,
                entities=[
                    Entity(
                        type="streaminfo",
                        stream_type="informative",
                        stream_sequence=self._sequence_number,
                    )
                ],
            )
            self._sequence_number += 1
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
        if self._cancelled:
            return
        if self._ended:
            raise RuntimeError("The stream has already ended.")

        # Update full message text
        self._message += text

        # If there are citations, modify the content so that the sources are numbers instead of [doc1], [doc2], etc.
        self._message = CitationUtil.format_citations_response(self._message)

        # Queue the next chunk
        self._queue_next_chunk()

    async def end_stream(self) -> None:
        """
        Ends the stream by sending the final message to the client.
        """
        if self._ended:
            raise RuntimeError("The stream has already ended.")

        # Queue final message
        self._ended = True
        self._queue_next_chunk()

        # Wait for the queue to drain
        await self.wait_for_queue()

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

    def _set_defaults(self, context: "TurnContext"):
        if context.activity.channel_id == Channels.ms_teams:
            self._is_streaming_channel = True
            self._interval = 1.0
        elif context.activity.channel_id == Channels.direct_line:
            self._is_streaming_channel = True
            self._interval = 0.5
        elif context.activity.delivery_mode == DeliveryModes.stream:
            self._is_streaming_channel = True
            self._interval = 0.1

        self._channel_id = context.activity.channel_id

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
                    entities=[
                        Entity(
                            type="streaminfo",
                            stream_type="final",
                            stream_sequence=self._sequence_number,
                        )
                    ],
                )
            elif self._is_streaming_channel:
                # Send typing activity
                activity = Activity(
                    type="typing",
                    text=self._message,
                    entities=[
                        Entity(
                            type="streaminfo",
                            stream_type="streaming",
                            stream_sequence=self._sequence_number,
                        )
                    ],
                )
            else:
                return
            self._sequence_number += 1
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
                if activity:
                    await self._send_activity(activity)
        except Exception as err:
            if (
                "403" in str(err)
                and self._context.activity.channel_id == Channels.ms_teams
            ):
                logger.warning("Teams channel stopped the stream.")
                self._cancelled = True
            else:
                logger.error(
                    f"Error occurred when sending activity while streaming: {err}"
                )
                raise
        finally:
            self._queue_sync = None

    async def _send_activity(self, activity: Activity) -> None:
        """
        Sends an activity to the client and saves the stream ID returned.

        Args:
            activity: The activity to send.
        """

        streaminfo_entity = None

        if not activity.entities:
            streaminfo_entity = Entity(type="streaminfo")
            activity.entities = [streaminfo_entity]
        else:
            for entity in activity.entities:
                if hasattr(entity, "type") and entity.type == "streaminfo":
                    streaminfo_entity = entity
                    break

            if not streaminfo_entity:
                # If no streaminfo entity exists, create one
                streaminfo_entity = Entity(type="streaminfo")
                activity.entities.append(streaminfo_entity)

        # Set activity ID to the assigned stream ID
        if self._stream_id:
            activity.id = self._stream_id
            streaminfo_entity.stream_id = self._stream_id

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
            if self._enable_feedback_loop and self._feedback_loop_type:
                # Add feedback loop to streaminfo entity
                streaminfo_entity.feedback_loop = {"type": self._feedback_loop_type}
            else:
                # Add feedback loop enabled to streaminfo entity
                streaminfo_entity.feedback_loop_enabled = self._enable_feedback_loop
        # Add in Generated by AI
        if self._enable_generated_by_ai_label:
            add_ai_to_activity(activity, self._citations, self._sensitivity_label)

        # Send activity
        response = await self._context.send_activity(activity)
        await asyncio.sleep(self._interval)

        # Save assigned stream ID
        if not self._stream_id and response:
            self._stream_id = response.id
