"""
Unit tests for the AgentClient class.

This module tests:
- AgentClient initialization
- Activity template handling
- _build_activity method
- send method
- send_expect_replies method
- invoke method
- get_all and get_new methods
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from microsoft_agents.testing.client.agent_client import AgentClient
from microsoft_agents.testing.client.exchange.sender import Sender
from microsoft_agents.testing.client.exchange.transcript import Transcript
from microsoft_agents.testing.client.exchange.exchange import Exchange
from microsoft_agents.testing.utils import ActivityTemplate, ModelTemplate
from microsoft_agents.activity import Activity, ActivityTypes, DeliveryModes, InvokeResponse


# =============================================================================
# Mock Helpers
# =============================================================================

class MockSender(Sender):
    """Mock Sender for testing."""
    
    def __init__(self, transcript: Transcript = None):
        super().__init__(transcript)
        self.send_mock = AsyncMock()
        self.last_sent_activity = None
    
    async def send(self, activity: Activity) -> Exchange:
        self.last_sent_activity = activity
        return await self.send_mock(activity)


def create_test_exchange(responses: list[Activity] = None) -> Exchange:
    """Create a test Exchange."""
    return Exchange(
        status_code=200,
        responses=responses or []
    )


# =============================================================================
# AgentClient Initialization Tests
# =============================================================================

class TestAgentClientInit:
    """Test AgentClient initialization."""
    
    def test_init_with_sender_and_transcript(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        
        client = AgentClient(sender=sender, transcript=transcript)
        
        assert client._sender is sender
        assert client._transcript is transcript
    
    def test_init_creates_default_template(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        
        client = AgentClient(sender=sender, transcript=transcript)
        
        assert client._template is not None
        assert isinstance(client._template, ModelTemplate)
    
    def test_init_with_custom_template(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        custom_template = ActivityTemplate()
        
        client = AgentClient(
            sender=sender,
            transcript=transcript,
            activity_template=custom_template
        )
        
        assert client._template is custom_template


# =============================================================================
# Template Property Tests
# =============================================================================

class TestAgentClientTemplate:
    """Test the template property."""
    
    def test_template_getter(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        template = client.template
        assert isinstance(template, ModelTemplate)
    
    def test_template_setter(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        new_template = ActivityTemplate()
        client.template = new_template
        
        assert client.template is new_template


# =============================================================================
# Build Activity Tests
# =============================================================================

class TestBuildActivity:
    """Test the _build_activity method."""
    
    def test_build_activity_from_string(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        activity = client._build_activity("hello world")
        
        assert isinstance(activity, Activity)
        assert activity.type == ActivityTypes.message
        assert activity.text == "hello world"
    
    def test_build_activity_from_activity(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        original = Activity(
            type=ActivityTypes.message,
            text="original",
            locale="en-US"
        )
        
        activity = client._build_activity(original)
        
        assert activity.text == "original"
        assert activity.locale == "en-US"


# =============================================================================
# Get All Tests
# =============================================================================

class TestAgentClientGetAll:
    """Test the get_all method."""
    
    def test_get_all_empty(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        result = client.get_all()
        
        assert result == []
    
    def test_get_all_returns_responses(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        # Add exchanges to transcript
        response1 = Activity(type=ActivityTypes.message, text="response1")
        response2 = Activity(type=ActivityTypes.message, text="response2")
        transcript.record(Exchange(responses=[response1]))
        transcript.record(Exchange(responses=[response2]))
        
        result = client.get_all()
        
        assert len(result) == 2
        assert result[0].text == "response1"
        assert result[1].text == "response2"
    
    def test_get_all_flattens_multiple_responses(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        # Exchange with multiple responses
        responses = [
            Activity(type=ActivityTypes.typing),
            Activity(type=ActivityTypes.message, text="first"),
            Activity(type=ActivityTypes.message, text="second"),
        ]
        transcript.record(Exchange(responses=responses))
        
        result = client.get_all()
        
        assert len(result) == 3


# =============================================================================
# Get New Tests
# =============================================================================

class TestAgentClientGetNew:
    """Test the get_new method."""
    
    def test_get_new_empty(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        result = client.get_new()
        
        assert result == []
    
    def test_get_new_returns_new_responses(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        response = Activity(type=ActivityTypes.message, text="new")
        transcript.record(Exchange(responses=[response]))
        
        result = client.get_new()
        
        assert len(result) == 1
        assert result[0].text == "new"
    
    def test_get_new_advances_cursor(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        transcript.record(Exchange(responses=[Activity(type=ActivityTypes.message, text="a")]))
        
        first_call = client.get_new()
        assert len(first_call) == 1
        
        second_call = client.get_new()
        assert len(second_call) == 0
    
    def test_get_new_only_returns_new(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        transcript.record(Exchange(responses=[Activity(type=ActivityTypes.message, text="a")]))
        client.get_new()  # Consume "a"
        
        transcript.record(Exchange(responses=[Activity(type=ActivityTypes.message, text="b")]))
        
        result = client.get_new()
        assert len(result) == 1
        assert result[0].text == "b"


# =============================================================================
# Invoke Method Tests
# =============================================================================

class TestAgentClientInvoke:
    """Test the invoke method."""
    
    @pytest.mark.asyncio
    async def test_invoke_requires_invoke_type(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        # Message type should raise
        activity = Activity(type=ActivityTypes.message, text="hello")
        
        with pytest.raises(ValueError, match="type must be 'invoke'"):
            await client.invoke(activity)
    
    @pytest.mark.asyncio
    async def test_invoke_returns_invoke_response(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        invoke_response = InvokeResponse(status=200, body={"result": "ok"})
        exchange = Exchange(invoke_response=invoke_response)
        sender.send_mock.return_value = exchange
        
        activity = Activity(type=ActivityTypes.invoke, name="test/action")
        
        result = await client.invoke(activity)
        
        assert result is invoke_response
        assert result.status == 200
    
    @pytest.mark.asyncio
    async def test_invoke_raises_on_no_response(self):
        transcript = Transcript()
        sender = MockSender(transcript)
        client = AgentClient(sender=sender, transcript=transcript)
        
        exchange = Exchange(invoke_response=None)
        sender.send_mock.return_value = exchange
        
        activity = Activity(type=ActivityTypes.invoke, name="test/action")
        
        with pytest.raises(RuntimeError, match="No InvokeResponse received"):
            await client.invoke(activity)
