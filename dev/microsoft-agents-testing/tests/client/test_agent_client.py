"""
Unit tests for the AgentClient class.

This module tests:
- AgentClient initialization
- Template property getter/setter
- Transcript property
- Activity building (_build_activity)
- send() method
- send_expect_replies() method
- invoke() method
- get_all() method
- get_new() method
- child() method
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)
from microsoft_agents.testing.client.agent_client import AgentClient
from microsoft_agents.testing.client.exchange import Sender, Exchange, Transcript
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_sender():
    """Create a mock Sender that records exchanges to the transcript."""
    sender = MagicMock()
    
    async def send_with_record(activity, transcript=None, **kwargs):
        # Get the exchange that was set as return_value
        exchange = sender.send._mock_return_value
        if transcript is not None:
            transcript.record(exchange)
        return exchange
    
    sender.send = AsyncMock(side_effect=send_with_record)
    return sender


@pytest.fixture
def mock_transcript():
    """Create a mock Transcript."""
    transcript = MagicMock(spec=Transcript)
    transcript.get_new.return_value = []
    transcript.get_all.return_value = []
    transcript.child.return_value = MagicMock(spec=Transcript)
    return transcript


@pytest.fixture
def mock_exchange():
    """Create a mock Exchange with default values."""
    exchange = MagicMock(spec=Exchange)
    exchange.responses = []
    exchange.invoke_response = None
    exchange.error = None
    return exchange


@pytest.fixture
def sample_activity():
    """Create a sample Activity for testing."""
    return Activity(type=ActivityTypes.message, text="Hello, World!")


@pytest.fixture
def sample_invoke_activity():
    """Create a sample invoke Activity for testing."""
    return Activity(type=ActivityTypes.invoke, name="test/invoke")


@pytest.fixture
def activity_template():
    """Create an ActivityTemplate for testing."""
    return ActivityTemplate({"channel_id": "test-channel"})


# =============================================================================
# AgentClient Initialization Tests
# =============================================================================

class TestAgentClientInit:
    """Test AgentClient initialization."""

    def test_init_with_sender_only(self, mock_sender):
        """Test initialization with only a sender."""
        client = AgentClient(mock_sender)
        
        assert client._sender is mock_sender
        assert isinstance(client._transcript, Transcript)
        assert isinstance(client._template, ActivityTemplate)

    def test_init_with_sender_and_transcript(self, mock_sender, mock_transcript):
        """Test initialization with sender and transcript."""
        client = AgentClient(mock_sender, transcript=mock_transcript)
        
        assert client._sender is mock_sender
        assert client._transcript is mock_transcript

    def test_init_with_all_parameters(self, mock_sender, mock_transcript, activity_template):
        """Test initialization with all parameters."""
        client = AgentClient(
            mock_sender,
            transcript=mock_transcript,
            activity_template=activity_template
        )
        
        assert client._sender is mock_sender
        assert client._transcript is mock_transcript
        assert client._template is activity_template

    def test_init_creates_default_transcript_when_none(self, mock_sender):
        """Test that a default Transcript is created when None is passed."""
        client = AgentClient(mock_sender, transcript=None)
        
        assert isinstance(client._transcript, Transcript)

    def test_init_creates_default_template_when_none(self, mock_sender):
        """Test that a default ActivityTemplate is created when None is passed."""
        client = AgentClient(mock_sender, activity_template=None)
        
        assert isinstance(client._template, ActivityTemplate)


# =============================================================================
# Template Property Tests
# =============================================================================

class TestAgentClientTemplateProperty:
    """Test AgentClient template property."""

    def test_template_getter(self, mock_sender, activity_template):
        """Test template property getter."""
        client = AgentClient(mock_sender, activity_template=activity_template)
        
        assert client.template is activity_template

    def test_template_setter(self, mock_sender):
        """Test template property setter."""
        client = AgentClient(mock_sender)
        new_template = ActivityTemplate({"channel_id": "new-channel"})
        
        client.template = new_template
        
        assert client.template is new_template


# =============================================================================
# Transcript Property Tests
# =============================================================================

class TestAgentClientTranscriptProperty:
    """Test AgentClient transcript property."""

    def test_transcript_getter(self, mock_sender, mock_transcript):
        """Test transcript property getter."""
        client = AgentClient(mock_sender, transcript=mock_transcript)
        
        assert client.transcript is mock_transcript


# =============================================================================
# _build_activity Tests
# =============================================================================

class TestAgentClientBuildActivity:
    """Test AgentClient._build_activity() method."""

    def test_build_activity_from_string(self, mock_sender):
        """Test building activity from a string."""
        client = AgentClient(mock_sender)
        
        activity = client._build_activity("Hello")
        
        assert isinstance(activity, Activity)
        assert activity.type == ActivityTypes.message
        assert activity.text == "Hello"

    def test_build_activity_from_activity(self, mock_sender, sample_activity):
        """Test building activity from an Activity."""
        client = AgentClient(mock_sender)
        
        activity = client._build_activity(sample_activity)
        
        assert isinstance(activity, Activity)
        assert activity.text == "Hello, World!"

    def test_build_activity_applies_template(self, mock_sender, activity_template):
        """Test that template is applied when building activity."""
        client = AgentClient(mock_sender, activity_template=activity_template)
        
        activity = client._build_activity("Test message")
        
        assert activity.channel_id == "test-channel"
        assert activity.text == "Test message"


# =============================================================================
# send() Method Tests
# =============================================================================

class TestAgentClientSend:
    """Test AgentClient.send() method."""

    @pytest.mark.asyncio
    async def test_send_with_string(self, mock_sender, mock_exchange):
        """Test send with a string message."""
        mock_sender.send.return_value = mock_exchange
        mock_exchange.responses = [Activity(type=ActivityTypes.message, text="Response")]
        client = AgentClient(mock_sender)
        
        responses = await client.send("Hello")
        
        mock_sender.send.assert_called_once()
        call_args = mock_sender.send.call_args
        assert call_args[0][0].text == "Hello"
        assert len(responses) == 1
        assert responses[0].text == "Response"

    @pytest.mark.asyncio
    async def test_send_with_activity(self, mock_sender, mock_exchange, sample_activity):
        """Test send with an Activity object."""
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.send(sample_activity)
        
        mock_sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_returns_exchange_responses(self, mock_sender, mock_exchange):
        """Test that send returns responses from exchange."""
        response1 = Activity(type=ActivityTypes.message, text="Response 1")
        response2 = Activity(type=ActivityTypes.message, text="Response 2")
        mock_exchange.responses = [response1, response2]
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        responses = await client.send("Hello")
        
        assert len(responses) == 2
        assert responses[0].text == "Response 1"
        assert responses[1].text == "Response 2"

    @pytest.mark.asyncio
    async def test_send_with_wait(self):
        """Test send with wait parameter."""
        # Create a sender that doesn't auto-record (for this specific test)
        sender = MagicMock()
        mock_exchange = MagicMock()
        mock_exchange.responses = [Activity(type=ActivityTypes.message, text="Immediate")]
        
        async def send_with_record(activity, transcript=None, **kwargs):
            if transcript is not None:
                transcript.record(mock_exchange)
            return mock_exchange
        
        sender.send = AsyncMock(side_effect=send_with_record)
        
        transcript = Transcript()
        client = AgentClient(sender, transcript=transcript)
        
        # Simulate additional response arriving during wait
        delayed_exchange = Exchange(
            responses=[Activity(type=ActivityTypes.message, text="Delayed")]
        )
        
        async def record_delayed():
            await asyncio.sleep(0.05)
            transcript.record(delayed_exchange)
        
        asyncio.create_task(record_delayed())
        
        responses = await client.send("Hello", wait=0.1)
        
        assert len(responses) == 2
        assert responses[0].text == "Immediate"
        assert responses[1].text == "Delayed"

    @pytest.mark.asyncio
    async def test_send_with_zero_wait(self, mock_sender, mock_exchange):
        """Test send with zero wait returns only immediate responses."""
        mock_exchange.responses = [Activity(type=ActivityTypes.message, text="Response")]
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        responses = await client.send("Hello", wait=0.0)
        
        assert len(responses) == 1

    @pytest.mark.asyncio
    async def test_send_with_negative_wait(self, mock_sender, mock_exchange):
        """Test send with negative wait is treated as zero."""
        mock_exchange.responses = [Activity(type=ActivityTypes.message, text="Response")]
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        responses = await client.send("Hello", wait=-1.0)
        
        assert len(responses) == 1

    @pytest.mark.asyncio
    async def test_send_passes_kwargs_to_sender(self, mock_sender, mock_exchange):
        """Test that additional kwargs are passed to sender."""
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.send("Hello", timeout=30, custom_param="value")
        
        call_kwargs = mock_sender.send.call_args[1]
        assert call_kwargs.get("timeout") == 30
        assert call_kwargs.get("custom_param") == "value"

    @pytest.mark.asyncio
    async def test_send_clears_new_before_sending(self, mock_sender, mock_exchange):
        """Test that get_new is called before sending to clear cursor."""
        mock_sender.send.return_value = mock_exchange
        transcript = MagicMock(spec=Transcript)
        transcript.get_new.return_value = []
        client = AgentClient(mock_sender, transcript=transcript)
        
        await client.send("Hello")
        
        # get_new should be called before send
        assert transcript.get_new.called


# =============================================================================
# send_expect_replies() Method Tests
# =============================================================================

class TestAgentClientSendExpectReplies:
    """Test AgentClient.send_expect_replies() method."""

    @pytest.mark.asyncio
    async def test_send_expect_replies_sets_delivery_mode(self, mock_sender, mock_exchange):
        """Test that delivery mode is set to expect_replies."""
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.send_expect_replies("Hello")
        
        call_args = mock_sender.send.call_args
        sent_activity = call_args[0][0]
        assert sent_activity.delivery_mode == DeliveryModes.expect_replies

    @pytest.mark.asyncio
    async def test_send_expect_replies_with_activity(self, mock_sender, mock_exchange, sample_activity):
        """Test send_expect_replies with Activity object."""
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.send_expect_replies(sample_activity)
        
        call_args = mock_sender.send.call_args
        sent_activity = call_args[0][0]
        assert sent_activity.delivery_mode == DeliveryModes.expect_replies

    @pytest.mark.asyncio
    async def test_send_expect_replies_passes_kwargs(self, mock_sender, mock_exchange):
        """Test that kwargs are passed through."""
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.send_expect_replies("Hello", timeout=30)
        
        call_kwargs = mock_sender.send.call_args[1]
        assert call_kwargs.get("timeout") == 30

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_responses(self, mock_sender, mock_exchange):
        """Test that responses are returned."""
        response = Activity(type=ActivityTypes.message, text="Reply")
        mock_exchange.responses = [response]
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        responses = await client.send_expect_replies("Hello")
        
        assert len(responses) == 1
        assert responses[0].text == "Reply"


# =============================================================================
# invoke() Method Tests
# =============================================================================

class TestAgentClientInvoke:
    """Test AgentClient.invoke() method."""

    @pytest.mark.asyncio
    async def test_invoke_with_valid_invoke_activity(self, mock_sender, mock_exchange, sample_invoke_activity):
        """Test invoke with a valid invoke activity."""
        mock_exchange.invoke_response = InvokeResponse(status=200, body={"result": "success"})
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        response = await client.invoke(sample_invoke_activity)
        
        assert response.status == 200
        assert response.body == {"result": "success"}

    @pytest.mark.asyncio
    async def test_invoke_raises_for_non_invoke_activity(self, mock_sender, sample_activity):
        """Test invoke raises ValueError for non-invoke activity."""
        client = AgentClient(mock_sender)
        
        with pytest.raises(ValueError) as exc_info:
            await client.invoke(sample_activity)
        
        assert "Activity type must be 'invoke'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_raises_when_no_invoke_response(self, mock_sender, mock_exchange, sample_invoke_activity):
        """Test invoke raises RuntimeError when no InvokeResponse received."""
        mock_exchange.invoke_response = None
        mock_exchange.error = None
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        with pytest.raises(RuntimeError) as exc_info:
            await client.invoke(sample_invoke_activity)
        
        assert "No InvokeResponse received" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_raises_exchange_error(self, mock_sender, mock_exchange, sample_invoke_activity):
        """Test invoke raises exception when exchange has error."""
        mock_exchange.invoke_response = None
        mock_exchange.error = "Connection failed"
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        with pytest.raises(Exception) as exc_info:
            await client.invoke(sample_invoke_activity)
        
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_passes_kwargs_to_sender(self, mock_sender, mock_exchange, sample_invoke_activity):
        """Test that kwargs are passed to sender."""
        mock_exchange.invoke_response = InvokeResponse(status=200)
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender)
        
        await client.invoke(sample_invoke_activity, timeout=30)
        
        call_kwargs = mock_sender.send.call_args[1]
        assert call_kwargs.get("timeout") == 30

    @pytest.mark.asyncio
    async def test_invoke_applies_template(self, mock_sender, mock_exchange, sample_invoke_activity, activity_template):
        """Test that template is applied to invoke activity."""
        mock_exchange.invoke_response = InvokeResponse(status=200)
        mock_sender.send.return_value = mock_exchange
        client = AgentClient(mock_sender, activity_template=activity_template)
        
        await client.invoke(sample_invoke_activity)
        
        call_args = mock_sender.send.call_args
        sent_activity = call_args[0][0]
        assert sent_activity.channel_id == "test-channel"


# =============================================================================
# get_all() Method Tests
# =============================================================================

class TestAgentClientGetAll:
    """Test AgentClient.get_all() method."""

    def test_get_all_returns_empty_list_initially(self, mock_sender):
        """Test get_all returns empty list when no exchanges."""
        client = AgentClient(mock_sender)
        
        result = client.get_all()
        
        assert result == []

    def test_get_all_returns_all_responses(self, mock_sender):
        """Test get_all returns all responses from all exchanges."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        # Record exchanges
        exchange1 = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="Response 1"),
            Activity(type=ActivityTypes.message, text="Response 2"),
        ])
        exchange2 = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="Response 3"),
        ])
        transcript.record(exchange1)
        transcript.record(exchange2)
        
        result = client.get_all()
        
        assert len(result) == 3
        assert result[0].text == "Response 1"
        assert result[1].text == "Response 2"
        assert result[2].text == "Response 3"

    def test_get_all_can_be_called_multiple_times(self, mock_sender):
        """Test get_all returns same results on multiple calls."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        exchange = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="Response"),
        ])
        transcript.record(exchange)
        
        result1 = client.get_all()
        result2 = client.get_all()
        
        assert len(result1) == 1
        assert len(result2) == 1


# =============================================================================
# get_new() Method Tests
# =============================================================================

class TestAgentClientGetNew:
    """Test AgentClient.get_new() method."""

    def test_get_new_returns_empty_list_initially(self, mock_sender):
        """Test get_new returns empty list when no new exchanges."""
        client = AgentClient(mock_sender)
        
        result = client.get_new()
        
        assert result == []

    def test_get_new_returns_new_responses(self, mock_sender):
        """Test get_new returns responses from new exchanges."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        exchange = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="New Response"),
        ])
        transcript.record(exchange)
        
        result = client.get_new()
        
        assert len(result) == 1
        assert result[0].text == "New Response"

    def test_get_new_advances_cursor(self, mock_sender):
        """Test get_new advances cursor so subsequent calls return only new items."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        exchange1 = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="First"),
        ])
        transcript.record(exchange1)
        
        result1 = client.get_new()
        assert len(result1) == 1
        
        # Second call should return empty (no new exchanges)
        result2 = client.get_new()
        assert len(result2) == 0
        
        # Add new exchange
        exchange2 = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="Second"),
        ])
        transcript.record(exchange2)
        
        # Third call should return only the new exchange
        result3 = client.get_new()
        assert len(result3) == 1
        assert result3[0].text == "Second"


# =============================================================================
# child() Method Tests
# =============================================================================

class TestAgentClientChild:
    """Test AgentClient.child() method."""

    def test_child_returns_new_agent_client(self, mock_sender):
        """Test child returns a new AgentClient instance."""
        client = AgentClient(mock_sender)
        
        child_client = client.child()
        
        assert isinstance(child_client, AgentClient)
        assert child_client is not client

    def test_child_shares_sender(self, mock_sender):
        """Test child shares the same sender."""
        client = AgentClient(mock_sender)
        
        child_client = client.child()
        
        assert child_client._sender is mock_sender

    def test_child_shares_template(self, mock_sender, activity_template):
        """Test child shares the same template."""
        client = AgentClient(mock_sender, activity_template=activity_template)
        
        child_client = client.child()
        
        assert child_client._template is activity_template

    def test_child_has_child_transcript(self, mock_sender):
        """Test child has a child transcript."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        child_client = client.child()
        
        # Child transcript should be different
        assert child_client._transcript is not transcript
        # Child transcript should have parent as the original transcript
        assert child_client._transcript._parent is transcript

    def test_child_transcript_propagates_to_parent(self, mock_sender):
        """Test that exchanges recorded in child propagate to parent."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        child_client = client.child()
        
        exchange = Exchange(responses=[
            Activity(type=ActivityTypes.message, text="Child Response"),
        ])
        child_client._transcript.record(exchange)
        
        # Parent should see the exchange
        parent_responses = client.get_all()
        child_responses = child_client.get_all()
        
        assert len(parent_responses) == 1
        assert len(child_responses) == 1
        assert parent_responses[0].text == "Child Response"


# =============================================================================
# Integration-style Tests
# =============================================================================

class TestAgentClientIntegration:
    """Integration-style tests for AgentClient."""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, mock_sender):
        """Test a complete conversation flow."""
        transcript = Transcript()
        client = AgentClient(mock_sender, transcript=transcript)
        
        # First exchange
        exchange1 = MagicMock(spec=Exchange)
        exchange1.responses = [Activity(type=ActivityTypes.message, text="Hello there!")]
        mock_sender.send.return_value = exchange1
        
        responses1 = await client.send("Hello")
        assert len(responses1) == 1
        assert responses1[0].text == "Hello there!"
        
        # Second exchange
        exchange2 = MagicMock(spec=Exchange)
        exchange2.responses = [Activity(type=ActivityTypes.message, text="I can help with that.")]
        mock_sender.send.return_value = exchange2
        
        responses2 = await client.send("Can you help me?")
        assert len(responses2) == 1
        
        # Check all responses
        all_responses = client.get_all()
        assert len(all_responses) == 2

    @pytest.mark.asyncio
    async def test_parent_child_conversation_isolation(self, mock_sender):
        """Test that parent and child have proper isolation and sharing."""
        parent_transcript = Transcript()
        parent_client = AgentClient(mock_sender, transcript=parent_transcript)
        child_client = parent_client.child()
        
        # Record in parent
        exchange1 = MagicMock(spec=Exchange)
        exchange1.responses = [Activity(type=ActivityTypes.message, text="Parent message")]
        mock_sender.send.return_value = exchange1
        await parent_client.send("From parent")
        
        # Record in child
        exchange2 = MagicMock(spec=Exchange)
        exchange2.responses = [Activity(type=ActivityTypes.message, text="Child message")]
        mock_sender.send.return_value = exchange2
        await child_client.send("From child")
        
        # Parent sees both (child propagates up)
        parent_all = parent_client.get_all()
        assert len(parent_all) == 2
        
        # Child only sees its own (parent doesn't propagate down)
        child_all = child_client.get_all()
        assert len(child_all) == 1
        assert child_all[0].text == "Child message"