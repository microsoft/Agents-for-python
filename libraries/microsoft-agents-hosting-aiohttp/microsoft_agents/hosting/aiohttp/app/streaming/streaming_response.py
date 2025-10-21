# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
import threading
from typing import List, Optional, Callable, Literal, TYPE_CHECKING
from dataclasses import dataclass

from microsoft_agents.activity import (
    Activity,
    Entity,
    Attachment,
    Channels,
    ClientCitation,
    DeliveryModes,
    SensitivityUsageInfo,
)

if TYPE_CHECKING:
    from microsoft_agents.hosting.core.turn_context import TurnContext

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
        self._queue: asyncio.Queue[Callable[[], Activity]] = asyncio.Queue()
        self._drain_task: Optional[asyncio.Task] = None
        self._drain_task_lock = asyncio.Lock()
        
        # State lock to protect shared mutable state (for async operations)
        self._state_lock = asyncio.Lock()
        # Sync lock for message text updates (can be called from sync context)
        self._message_lock = threading.Lock()
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
        Note: Returns a snapshot; may be stale if called during concurrent updates.
        """
        return self._stream_id

    @property
    def citations(self) -> Optional[List[ClientCitation]]:
        """
        Gets the citations of the current response.
        Note: Returns reference to internal list; do not modify directly.
        """
        return self._citations

    @property
    def updates_sent(self) -> int:
        """
        Gets the number of updates sent for the stream.
        Note: Returns a snapshot; may be stale if called during concurrent updates.
        """
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

        # Queue a typing activity - capture sequence number atomically
        async def create_activity_async():
            async with self._state_lock:
                seq_num = self._sequence_number
                self._sequence_number += 1
            
            activity = Activity(
                type="typing",
                text=text,
                entities=[
                    Entity(
                        type="streaminfo",
                        stream_type="informative",
                        stream_sequence=seq_num,
                    )
                ],
            )
            return activity

        self._queue_activity(create_activity_async)

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
        # Update message text synchronously under thread lock
        with self._message_lock:
            if self._cancelled:
                return
            if self._ended:
                raise RuntimeError("The stream has already ended.")

            # Update full message text atomically
            self._message += text
            # If there are citations, modify the content so that the sources are numbers instead of [doc1], [doc2], etc.
            self._message = CitationUtil.format_citations_response(self._message)

        # Schedule the async queueing work in background
        asyncio.create_task(self._queue_next_chunk())

    async def end_stream(self) -> None:
        """
        Ends the stream by sending the final message to the client.
        """
        async with self._state_lock:
            if self._ended:
                raise RuntimeError("The stream has already ended.")
            # Queue final message
            self._ended = True
        
        await self._queue_next_chunk()

        # Wait for the queue to drain
        await self.wait_for_queue()
        
        # Clean up any remaining tasks
        await self.cleanup()

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
        
        Note: This method schedules the citation update atomically but does not block.
        """
        if not citations:
            return
        
        # Build new citations outside of lock
        async def update_citations():
            async with self._state_lock:
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
        
        # Schedule the update to run in the event loop
        asyncio.create_task(update_citations())

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
        with self._message_lock:
            return self._message

    async def wait_for_queue(self) -> None:
        """
        Waits for the outgoing activity queue to be empty.
        """
        await self._queue.join()
        
        async with self._drain_task_lock:
            drain_task = self._drain_task
        
        if drain_task:
            await drain_task

    async def cleanup(self) -> None:
        """
        Cleans up resources and cancels any running tasks.
        Should be called when the StreamingResponse is no longer needed.
        """
        async with self._drain_task_lock:
            drain_task = self._drain_task
            self._drain_task = None
        
        if drain_task and not drain_task.done():
            drain_task.cancel()
            try:
                await drain_task
            except asyncio.CancelledError:
                logger.debug("Queue drain task was cancelled during cleanup.")
            except Exception as err:
                logger.warning(f"Error while cleaning up queue drain task: {err}")
        
        # Clear any remaining queue items to prevent memory leaks
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            else:
                self._queue.task_done()

    async def cancel(self) -> None:
        """
        Cancels the streaming response and cleans up resources.
        """
        async with self._state_lock:
            self._cancelled = True
        await self.cleanup()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.cleanup()

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

    async def _queue_next_chunk(self) -> None:
        """
        Queues the next chunk of text to be sent to the client.
        """
        # Are we already waiting to send a chunk? (check atomically)
        async with self._state_lock:
            if self._chunk_queued:
                return
            self._chunk_queued = True

        # Create activity factory that captures current state
        async def create_activity():
            # Capture message text under thread lock
            with self._message_lock:
                message = self._message
            
            async with self._state_lock:
                if self._ended:
                    # Send final message
                    activity = Activity(
                        type="message",
                        text=message or "end stream response",
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
                        text=message,
                        entities=[
                            Entity(
                                type="streaminfo",
                                stream_type="streaming",
                                stream_sequence=self._sequence_number,
                            )
                        ],
                    )
                else:
                    self._chunk_queued = False
                    return None
                
                self._sequence_number += 1
                self._chunk_queued = False
                return activity

        self._queue_activity(create_activity)

    def _queue_activity(self, factory: Callable[[], Activity]) -> None:
        """
        Queues an activity to be sent to the client.
        """
        self._queue.put_nowait(factory)

        # Ensure a drain task is running to process the queue
        async def ensure_drain_task():
            async with self._drain_task_lock:
                if not self._drain_task or self._drain_task.done():
                    try:
                        self._drain_task = asyncio.create_task(self._drain_queue())
                    except Exception as err:
                        logger.error(f"Failed to create drain task: {err}")
                        self._drain_task = None
                        raise

        asyncio.create_task(ensure_drain_task())

    async def _drain_queue(self) -> None:
        """
        Sends any queued activities to the client until the queue is empty.
        """
        try:
            logger.debug("Draining queue with %s activities.", self._queue.qsize())
            while True:
                # Check cancellation flag under lock
                async with self._state_lock:
                    if self._cancelled:
                        break
                
                try:
                    factory = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                try:
                    activity = await factory()
                    # Check cancellation again before sending
                    async with self._state_lock:
                        cancelled = self._cancelled
                    if activity and not cancelled:
                        await self._send_activity(activity)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            logger.debug("Queue drain task was cancelled.")
            raise
        except Exception as err:
            if (
                "403" in str(err)
                and self._context.activity.channel_id == Channels.ms_teams
            ):
                logger.warning("Teams channel stopped the stream.")
                async with self._state_lock:
                    self._cancelled = True
            else:
                logger.error(
                    f"Error occurred when sending activity while streaming: {err}"
                )
                raise
        finally:
            # Always clean up the task reference
            async with self._drain_task_lock:
                self._drain_task = None

    async def _send_activity(self, activity: Activity) -> None:
        """
        Sends an activity to the client and saves the stream ID returned.

        Args:
            activity: The activity to send.
        """
        # Capture message under thread lock
        with self._message_lock:
            message = self._message
        
        # Capture other state snapshot under async lock
        async with self._state_lock:
            stream_id = self._stream_id
            citations = self._citations
            ended = self._ended
            enable_feedback_loop = self._enable_feedback_loop
            feedback_loop_type = self._feedback_loop_type
            enable_generated_by_ai_label = self._enable_generated_by_ai_label
            sensitivity_label = self._sensitivity_label

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
        if stream_id:
            activity.id = stream_id
            streaminfo_entity.stream_id = stream_id

        if citations and len(citations) > 0 and not ended:
            # Filter out the citations unused in content.
            curr_citations = CitationUtil.get_used_citations(message, citations)
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
        if ended:
            if enable_feedback_loop and feedback_loop_type:
                # Add feedback loop to streaminfo entity
                streaminfo_entity.feedback_loop = {"type": feedback_loop_type}
            else:
                # Add feedback loop enabled to streaminfo entity
                streaminfo_entity.feedback_loop_enabled = enable_feedback_loop
        # Add in Generated by AI
        if enable_generated_by_ai_label:
            activity.add_ai_metadata(citations, sensitivity_label)

        # Send activity
        response = await self._context.send_activity(activity)
        await asyncio.sleep(self._interval)

        # Save assigned stream ID atomically
        async with self._state_lock:
            if not self._stream_id and response:
                self._stream_id = response.id
