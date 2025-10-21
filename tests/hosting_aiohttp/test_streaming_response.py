# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    Channels,
    ConversationAccount,
    DeliveryModes,
    Entity,
    ResourceResponse,
)
from microsoft_agents.hosting.core import TurnContext, ChannelAdapter
from microsoft_agents.hosting.aiohttp.app.streaming import StreamingResponse, Citation


class MockAdapter(ChannelAdapter):
    """Mock adapter for testing."""

    def __init__(self):
        self.sent_activities = []
        self._response_id = 1

    async def send_activities(self, context, activities):
        responses = []
        for activity in activities:
            self.sent_activities.append(activity)
            responses.append(ResourceResponse(id=f"response_{self._response_id}"))
            self._response_id += 1
        return responses

    async def update_activity(self, context, activity):
        return ResourceResponse(id=activity.id)

    async def delete_activity(self, context, reference):
        pass


def create_test_activity(
    channel_id: str = Channels.direct_line,
    delivery_mode: str = DeliveryModes.normal,
) -> Activity:
    """Create a test activity."""
    return Activity(
        type=ActivityTypes.message,
        id="test-activity-id",
        text="test message",
        from_property=ChannelAccount(id="user-id", name="User"),
        recipient=ChannelAccount(id="bot-id", name="Bot"),
        conversation=ConversationAccount(id="conversation-id"),
        channel_id=channel_id,
        service_url="https://test.example.com",
        delivery_mode=delivery_mode,
    )


@pytest.fixture
def mock_adapter():
    """Create a mock adapter."""
    return MockAdapter()


@pytest.fixture
def turn_context(mock_adapter):
    """Create a turn context for testing."""
    activity = create_test_activity()
    return TurnContext(mock_adapter, activity)


@pytest.fixture
def streaming_context(mock_adapter):
    """Create a turn context with streaming enabled (DirectLine)."""
    activity = create_test_activity(channel_id=Channels.direct_line)
    return TurnContext(mock_adapter, activity)


@pytest.fixture
def teams_context(mock_adapter):
    """Create a turn context for Teams channel."""
    activity = create_test_activity(channel_id=Channels.ms_teams)
    return TurnContext(mock_adapter, activity)


@pytest.fixture
def delivery_mode_context(mock_adapter):
    """Create a turn context with delivery mode set to stream."""
    activity = create_test_activity(
        channel_id="custom-channel", delivery_mode=DeliveryModes.stream
    )
    return TurnContext(mock_adapter, activity)


class TestStreamingResponseInitialization:
    """Test StreamingResponse initialization and configuration."""

    def test_init_basic(self, turn_context):
        """Test basic initialization."""
        response = StreamingResponse(turn_context)
        assert response._context == turn_context
        assert response._sequence_number == 1
        assert response._stream_id is None
        assert response._message == ""
        assert response._ended is False
        assert response._cancelled is False

    def test_init_direct_line_sets_streaming_channel(self, streaming_context):
        """Test DirectLine channel enables streaming."""
        response = StreamingResponse(streaming_context)
        assert response._is_streaming_channel is True
        assert response._interval == 0.5

    def test_init_teams_sets_streaming_channel(self, teams_context):
        """Test Teams channel enables streaming."""
        response = StreamingResponse(teams_context)
        assert response._is_streaming_channel is True
        assert response._interval == 1.0

    def test_init_delivery_mode_stream(self, delivery_mode_context):
        """Test delivery_mode='stream' enables streaming."""
        response = StreamingResponse(delivery_mode_context)
        assert response._is_streaming_channel is True
        assert response._interval == 0.1


class TestStreamingResponseProperties:
    """Test StreamingResponse properties."""

    def test_stream_id_property_initial(self, turn_context):
        """Test stream_id property returns None initially."""
        response = StreamingResponse(turn_context)
        assert response.stream_id is None

    def test_citations_property_initial(self, turn_context):
        """Test citations property returns empty list initially."""
        response = StreamingResponse(turn_context)
        assert response.citations == []

    def test_updates_sent_property_initial(self, turn_context):
        """Test updates_sent property returns 0 initially."""
        response = StreamingResponse(turn_context)
        assert response.updates_sent == 0


class TestQueueInformativeUpdate:
    """Test queue_informative_update method."""

    @pytest.mark.asyncio
    async def test_queue_informative_update_non_streaming_channel(self, turn_context):
        """Test informative update is not queued for non-streaming channels."""
        # Create context with non-streaming channel
        activity = create_test_activity(channel_id="non-streaming")
        context = TurnContext(MockAdapter(), activity)
        response = StreamingResponse(context)

        response.queue_informative_update("test message")
        await asyncio.sleep(0.1)  # Allow queue to process

        # Should not queue anything for non-streaming channels
        assert context.adapter.sent_activities == []

    @pytest.mark.asyncio
    async def test_queue_informative_update_streaming_channel(self, streaming_context):
        """Test informative update is queued for streaming channels."""
        response = StreamingResponse(streaming_context)

        response.queue_informative_update("Starting process...")
        await response.wait_for_queue()

        assert len(streaming_context.adapter.sent_activities) == 1
        activity = streaming_context.adapter.sent_activities[0]
        assert activity.type == "typing"
        assert activity.text == "Starting process..."
        assert len(activity.entities) == 1
        assert activity.entities[0].type == "streaminfo"
        assert activity.entities[0].stream_type == "informative"
        assert activity.entities[0].stream_sequence == 1

    @pytest.mark.asyncio
    async def test_queue_informative_update_raises_after_ended(self, streaming_context):
        """Test informative update raises error after stream ended."""
        response = StreamingResponse(streaming_context)
        await response.end_stream()

        with pytest.raises(RuntimeError, match="stream has already ended"):
            response.queue_informative_update("test")


class TestQueueTextChunk:
    """Test queue_text_chunk method."""

    @pytest.mark.asyncio
    async def test_queue_text_chunk_simple(self, streaming_context):
        """Test queueing a simple text chunk."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("Hello ")
        await response.wait_for_queue()

        assert len(streaming_context.adapter.sent_activities) == 1
        activity = streaming_context.adapter.sent_activities[0]
        assert activity.type == "typing"
        assert activity.text == "Hello "

    @pytest.mark.asyncio
    async def test_queue_text_chunk_multiple(self, streaming_context):
        """Test queueing multiple text chunks."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("Hello ")
        await response.queue_text_chunk("World")
        await response.queue_text_chunk("!")
        await response.wait_for_queue()

        # Message should accumulate
        assert response.get_message() == "Hello World!"
        assert len(streaming_context.adapter.sent_activities) >= 1

    @pytest.mark.asyncio
    async def test_queue_text_chunk_cancelled(self, streaming_context):
        """Test queueing text chunk after cancellation."""
        response = StreamingResponse(streaming_context)
        await response.cancel()

        # Should not raise, just return silently
        await response.queue_text_chunk("test")
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_queue_text_chunk_raises_after_ended(self, streaming_context):
        """Test queueing text chunk after stream ended raises error."""
        response = StreamingResponse(streaming_context)
        await response.queue_text_chunk("test")
        await response.end_stream()

        with pytest.raises(RuntimeError, match="stream has already ended"):
            await response.queue_text_chunk("more")

    @pytest.mark.asyncio
    async def test_queue_text_chunk_updates_sequence(self, streaming_context):
        """Test that text chunks increment sequence number."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("chunk1")
        await response.wait_for_queue()  # Wait for first chunk to be sent
        
        await response.queue_text_chunk("chunk2")
        await response.wait_for_queue()  # Wait for second chunk to be sent

        # Updates_sent should reflect the number of activities sent
        # Each chunk should result in at least one activity
        assert response.updates_sent >= 2


class TestEndStream:
    """Test end_stream method."""

    @pytest.mark.asyncio
    async def test_end_stream_sends_final_message(self, streaming_context):
        """Test end_stream sends a final message activity."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("Hello World")
        await response.end_stream()

        # Find the final message
        final_activities = [
            a for a in streaming_context.adapter.sent_activities if a.type == "message"
        ]
        assert len(final_activities) == 1
        activity = final_activities[0]
        assert activity.text == "Hello World"
        assert any(
            e.type == "streaminfo" and e.stream_type == "final"
            for e in activity.entities
        )

    @pytest.mark.asyncio
    async def test_end_stream_twice_raises_error(self, streaming_context):
        """Test calling end_stream twice raises error."""
        response = StreamingResponse(streaming_context)

        await response.end_stream()

        with pytest.raises(RuntimeError, match="stream has already ended"):
            await response.end_stream()

    @pytest.mark.asyncio
    async def test_end_stream_with_empty_message(self, streaming_context):
        """Test end_stream with no text queued."""
        response = StreamingResponse(streaming_context)
        await response.end_stream()

        final_activities = [
            a for a in streaming_context.adapter.sent_activities if a.type == "message"
        ]
        assert len(final_activities) == 1
        assert final_activities[0].text == "end stream response"


class TestSetAttachments:
    """Test set_attachments method."""

    @pytest.mark.asyncio
    async def test_set_attachments(self, streaming_context):
        """Test setting attachments on final message."""
        from microsoft_agents.activity import Attachment

        response = StreamingResponse(streaming_context)

        attachments = [
            Attachment(content_type="text/plain", content="test attachment")
        ]
        response.set_attachments(attachments)
        await response.end_stream()

        final_activities = [
            a for a in streaming_context.adapter.sent_activities if a.type == "message"
        ]
        assert len(final_activities) == 1
        assert final_activities[0].attachments == attachments


class TestSetCitations:
    """Test set_citations method."""

    @pytest.mark.asyncio
    async def test_set_citations(self, streaming_context):
        """Test setting citations."""
        response = StreamingResponse(streaming_context)

        citations = [
            Citation(
                title="Source 1",
                content="Content 1",
                filepath="file1.txt",
                url="http://example.com/1",
            ),
            Citation(
                title="Source 2",
                content="Content 2",
                filepath="file2.txt",
                url="http://example.com/2",
            ),
        ]

        await response.set_citations(citations)

        assert response.citations is not None
        assert len(response.citations) == 2
        assert response.citations[0].position == 1
        assert response.citations[1].position == 2

    @pytest.mark.asyncio
    async def test_set_citations_multiple_calls(self, streaming_context):
        """Test setting citations multiple times appends."""
        response = StreamingResponse(streaming_context)

        citations1 = [
            Citation(
                title="Source 1",
                content="Content 1",
                filepath="file1.txt",
                url="http://example.com/1",
            )
        ]
        await response.set_citations(citations1)

        citations2 = [
            Citation(
                title="Source 2",
                content="Content 2",
                filepath="file2.txt",
                url="http://example.com/2",
            )
        ]
        await response.set_citations(citations2)

        assert len(response.citations) == 2


class TestFeedbackAndLabels:
    """Test feedback loop and AI label settings."""

    def test_set_feedback_loop(self, turn_context):
        """Test setting feedback loop."""
        response = StreamingResponse(turn_context)
        response.set_feedback_loop(True)
        assert response._enable_feedback_loop is True

    def test_set_feedback_loop_type(self, turn_context):
        """Test setting feedback loop type."""
        response = StreamingResponse(turn_context)
        response.set_feedback_loop_type("custom")
        assert response._feedback_loop_type == "custom"

    def test_set_generated_by_ai_label(self, turn_context):
        """Test setting generated by AI label."""
        response = StreamingResponse(turn_context)
        response.set_generated_by_ai_label(True)
        assert response._enable_generated_by_ai_label is True


class TestGetMessage:
    """Test get_message method."""

    @pytest.mark.asyncio
    async def test_get_message_initial(self, turn_context):
        """Test get_message returns empty string initially."""
        response = StreamingResponse(turn_context)
        assert response.get_message() == ""

    @pytest.mark.asyncio
    async def test_get_message_after_chunks(self, streaming_context):
        """Test get_message returns accumulated text."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("Hello ")
        await response.queue_text_chunk("World")

        assert response.get_message() == "Hello World"


class TestWaitForQueue:
    """Test wait_for_queue method."""

    @pytest.mark.asyncio
    async def test_wait_for_queue_empty(self, turn_context):
        """Test wait_for_queue returns immediately when queue is empty."""
        response = StreamingResponse(turn_context)
        await response.wait_for_queue()  # Should not hang

    @pytest.mark.asyncio
    async def test_wait_for_queue_processes_all(self, streaming_context):
        """Test wait_for_queue waits for all items to process."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("chunk1")
        await response.wait_for_queue()  # Wait for chunk to be sent

        await response.queue_text_chunk("chunk2")
        await response.wait_for_queue()  # Wait for chunk to be sent

        await response.queue_text_chunk("chunk3")
        await response.wait_for_queue()  # Wait for chunk to be sent
        await response.wait_for_queue()

        # All activities should be sent
        assert len(streaming_context.adapter.sent_activities) >= 3


class TestCleanupAndCancel:
    """Test cleanup and cancel methods."""

    @pytest.mark.asyncio
    async def test_cleanup(self, streaming_context):
        """Test cleanup method."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("test")
        await response.cleanup()

        # Queue should be empty after cleanup
        assert response._queue.empty()

    @pytest.mark.asyncio
    async def test_cancel(self, streaming_context):
        """Test cancel method."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("test")
        await response.cancel()

        # Cancelled flag should be set
        assert response._cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_stops_processing(self, streaming_context):
        """Test cancel stops further processing."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("chunk1")
        await response.cancel()

        # Subsequent chunks should not raise, just be ignored
        await response.queue_text_chunk("chunk2")
        await asyncio.sleep(0.1)


class TestContextManager:
    """Test async context manager protocol."""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, streaming_context):
        """Test context manager calls cleanup on exit."""
        async with StreamingResponse(streaming_context) as response:
            await response.queue_text_chunk("test")

        # After exiting context, cleanup should have been called
        assert response._queue.empty()

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, streaming_context):
        """Test context manager cleans up even with exception."""
        try:
            async with StreamingResponse(streaming_context) as response:
                await response.queue_text_chunk("test")
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Cleanup should still have been called
        assert response._queue.empty()


class TestStreamIdAssignment:
    """Test stream ID assignment."""

    @pytest.mark.asyncio
    async def test_stream_id_assigned_after_first_send(self, streaming_context):
        """Test stream_id is assigned after first activity is sent."""
        response = StreamingResponse(streaming_context)

        assert response.stream_id is None

        await response.queue_text_chunk("test")
        await response.wait_for_queue()

        # Stream ID should be assigned after sending
        assert response.stream_id is not None
        assert response.stream_id.startswith("response_")

    @pytest.mark.asyncio
    async def test_stream_id_consistent_across_activities(self, streaming_context):
        """Test all activities in stream use same stream ID."""
        response = StreamingResponse(streaming_context)

        await response.queue_text_chunk("chunk1")
        await response.wait_for_queue()

        first_stream_id = response.stream_id

        await response.queue_text_chunk("chunk2")
        await response.wait_for_queue()

        assert response.stream_id == first_stream_id


class TestSequenceNumbers:
    """Test sequence number management."""

    @pytest.mark.asyncio
    async def test_sequence_numbers_increment(self, streaming_context):
        """Test sequence numbers increment correctly."""
        response = StreamingResponse(streaming_context)

        response.queue_informative_update("info1")
        await response.queue_text_chunk("chunk1")
        await response.queue_text_chunk("chunk2")
        await response.wait_for_queue()

        # Each activity should have increasing sequence numbers
        for i, activity in enumerate(streaming_context.adapter.sent_activities):
            stream_entity = next(
                (e for e in activity.entities if e.type == "streaminfo"), None
            )
            assert stream_entity is not None
            assert stream_entity.stream_sequence == i + 1
