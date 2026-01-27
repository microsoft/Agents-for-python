"""
Unit tests for the ConversationClient class.

This module tests:
- ConversationClient initialization
- timeout property getter/setter
- transcript property
- say() method (with expect_replies and without)
- wait_for() method
- expect() method
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import asyncio

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.client.conversation_client import ConversationClient
from microsoft_agents.testing.client.agent_client import AgentClient
from microsoft_agents.testing.client.exchange import Transcript


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_transcript():
    """Create a mock Transcript."""
    transcript = MagicMock(spec=Transcript)
    transcript.get_new.return_value = []
    transcript.get_all.return_value = []
    return transcript


@pytest.fixture
def mock_child_client(mock_transcript):
    """Create a mock child AgentClient."""
    child_client = MagicMock(spec=AgentClient)
    child_client.transcript = mock_transcript
    child_client.send = AsyncMock(return_value=[])
    child_client.send_expect_replies = AsyncMock(return_value=[])
    child_client.get_new = MagicMock(return_value=[])
    return child_client


@pytest.fixture
def mock_agent_client(mock_child_client):
    """Create a mock AgentClient that returns a child client."""
    agent_client = MagicMock(spec=AgentClient)
    agent_client.child.return_value = mock_child_client
    return agent_client


@pytest.fixture
def sample_activities():
    """Create sample activities for testing."""
    return [
        Activity(type=ActivityTypes.message, text="Hello!"),
        Activity(type=ActivityTypes.message, text="How are you?"),
    ]


@pytest.fixture
def typing_activity():
    """Create a typing activity for testing."""
    return Activity(type=ActivityTypes.typing)


# =============================================================================
# ConversationClient Initialization Tests
# =============================================================================

class TestConversationClientInit:
    """Test ConversationClient initialization."""

    def test_init_with_agent_client_only(self, mock_agent_client, mock_child_client, mock_transcript):
        """Test initialization with only an agent client."""
        client = ConversationClient(mock_agent_client)
        
        mock_agent_client.child.assert_called_once()
        assert client._client is mock_child_client
        assert client._transcript is mock_transcript
        assert client._expect_replies is False
        assert client._timeout is None

    def test_init_with_expect_replies_true(self, mock_agent_client, mock_child_client):
        """Test initialization with expect_replies set to True."""
        client = ConversationClient(mock_agent_client, expect_replies=True)
        
        assert client._expect_replies is True

    def test_init_with_expect_replies_false(self, mock_agent_client, mock_child_client):
        """Test initialization with expect_replies set to False."""
        client = ConversationClient(mock_agent_client, expect_replies=False)
        
        assert client._expect_replies is False

    def test_init_with_timeout(self, mock_agent_client, mock_child_client):
        """Test initialization with a timeout value."""
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        assert client._timeout == 5.0

    def test_init_with_all_parameters(self, mock_agent_client, mock_child_client):
        """Test initialization with all parameters."""
        client = ConversationClient(
            mock_agent_client,
            expect_replies=True,
            timeout=10.0
        )
        
        assert client._expect_replies is True
        assert client._timeout == 10.0


# =============================================================================
# Timeout Property Tests
# =============================================================================

class TestConversationClientTimeoutProperty:
    """Test ConversationClient timeout property."""

    def test_timeout_getter(self, mock_agent_client):
        """Test timeout property getter."""
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        assert client.timeout == 5.0

    def test_timeout_getter_none(self, mock_agent_client):
        """Test timeout property getter when None."""
        client = ConversationClient(mock_agent_client)
        
        assert client.timeout is None

    def test_timeout_setter(self, mock_agent_client):
        """Test timeout property setter."""
        client = ConversationClient(mock_agent_client)
        
        client.timeout = 10.0
        
        assert client.timeout == 10.0
        assert client._timeout == 10.0

    def test_timeout_setter_to_none(self, mock_agent_client):
        """Test timeout property setter to None."""
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        client.timeout = None
        
        assert client.timeout is None


# =============================================================================
# Transcript Property Tests
# =============================================================================

class TestConversationClientTranscriptProperty:
    """Test ConversationClient transcript property."""

    def test_transcript_getter(self, mock_agent_client, mock_transcript):
        """Test transcript property getter."""
        client = ConversationClient(mock_agent_client)
        
        assert client.transcript is mock_transcript


# =============================================================================
# Say Method Tests
# =============================================================================

class TestConversationClientSay:
    """Test ConversationClient say() method."""

    @pytest.mark.asyncio
    async def test_say_without_expect_replies(self, mock_agent_client, mock_child_client, sample_activities):
        """Test say() when expect_replies is False (default)."""
        mock_child_client.send.return_value = sample_activities
        client = ConversationClient(mock_agent_client, expect_replies=False)
        
        result = await client.say("Hello")
        
        mock_child_client.send.assert_called_once_with("Hello", wait=None, timeout=None)
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_say_with_expect_replies(self, mock_agent_client, mock_child_client, sample_activities):
        """Test say() when expect_replies is True."""
        mock_child_client.send_expect_replies.return_value = sample_activities
        client = ConversationClient(mock_agent_client, expect_replies=True)
        
        result = await client.say("Hello")
        
        mock_child_client.send_expect_replies.assert_called_once_with("Hello", timeout=None)
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_say_with_timeout(self, mock_agent_client, mock_child_client, sample_activities):
        """Test say() passes timeout to underlying client."""
        mock_child_client.send.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        result = await client.say("Hello")
        
        mock_child_client.send.assert_called_once_with("Hello", wait=None, timeout=5.0)

    @pytest.mark.asyncio
    async def test_say_with_expect_replies_and_timeout(self, mock_agent_client, mock_child_client, sample_activities):
        """Test say() with expect_replies=True passes timeout."""
        mock_child_client.send_expect_replies.return_value = sample_activities
        client = ConversationClient(mock_agent_client, expect_replies=True, timeout=3.0)
        
        result = await client.say("Hello")
        
        mock_child_client.send_expect_replies.assert_called_once_with("Hello", timeout=3.0)

    @pytest.mark.asyncio
    async def test_say_with_wait_parameter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test say() with wait parameter."""
        mock_child_client.send.return_value = sample_activities
        client = ConversationClient(mock_agent_client)
        
        result = await client.say("Hello", wait=2.0)
        
        mock_child_client.send.assert_called_once_with("Hello", wait=2.0, timeout=None)

    @pytest.mark.asyncio
    async def test_say_returns_empty_list_when_no_responses(self, mock_agent_client, mock_child_client):
        """Test say() returns empty list when no responses."""
        mock_child_client.send.return_value = []
        client = ConversationClient(mock_agent_client)
        
        result = await client.say("Hello")
        
        assert result == []


# =============================================================================
# Wait For Method Tests
# =============================================================================

class TestConversationClientWaitFor:
    """Test ConversationClient wait_for() method."""

    @pytest.mark.asyncio
    async def test_wait_for_returns_immediately_when_match_found(self, mock_agent_client, mock_child_client, sample_activities):
        """Test wait_for() returns immediately when matching activities are found."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        result = await client.wait_for(type=ActivityTypes.message)
        
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_wait_for_with_dict_filter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test wait_for() with a dict filter."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        result = await client.wait_for({"type": ActivityTypes.message})
        
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_wait_for_with_callable_filter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test wait_for() with a callable filter."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        filter_func = lambda x: x["type"] == ActivityTypes.message
        result = await client.wait_for(filter_func)
        
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_wait_for_polls_until_match(self, mock_agent_client, mock_child_client, sample_activities):
        """Test wait_for() polls until a match is found."""
        # First two calls return empty, third returns activities
        mock_child_client.get_new.side_effect = [[], [], sample_activities]
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        result = await client.wait_for(type=ActivityTypes.message)
        
        assert result == sample_activities
        assert mock_child_client.get_new.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_for_timeout_raises_timeout_error(self, mock_agent_client, mock_child_client):
        """Test wait_for() raises TimeoutError when timeout is exceeded."""
        mock_child_client.get_new.return_value = []  # Never matches
        client = ConversationClient(mock_agent_client, timeout=0.2)
        
        with pytest.raises(asyncio.TimeoutError):
            await client.wait_for(type=ActivityTypes.message)

    @pytest.mark.asyncio
    async def test_wait_for_with_no_filter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test wait_for() with no filter returns any activities."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        # With no filter, any activity should match
        result = await client.wait_for()
        
        assert result == sample_activities


# =============================================================================
# Expect Method Tests
# =============================================================================

class TestConversationClientExpect:
    """Test ConversationClient expect() method."""

    @pytest.mark.asyncio
    async def test_expect_succeeds_when_match_found(self, mock_agent_client, mock_child_client, sample_activities):
        """Test expect() succeeds when matching activities are found."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        # Should not raise
        await client.expect(type=ActivityTypes.message)

    @pytest.mark.asyncio
    async def test_expect_raises_assertion_error_on_timeout(self, mock_agent_client, mock_child_client):
        """Test expect() raises AssertionError when timeout is exceeded."""
        mock_child_client.get_new.return_value = []  # Never matches
        client = ConversationClient(mock_agent_client, timeout=0.2)
        
        with pytest.raises(AssertionError, match="Timeout waiting for expected activities"):
            await client.expect(type=ActivityTypes.message)

    @pytest.mark.asyncio
    async def test_expect_with_dict_filter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test expect() with a dict filter."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        # Should not raise
        await client.expect({"type": ActivityTypes.message})

    @pytest.mark.asyncio
    async def test_expect_with_callable_filter(self, mock_agent_client, mock_child_client, sample_activities):
        """Test expect() with a callable filter."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        filter_func = lambda x: x["type"] == ActivityTypes.message
        
        # Should not raise
        await client.expect(filter_func)

    @pytest.mark.asyncio
    async def test_expect_with_kwargs(self, mock_agent_client, mock_child_client, sample_activities):
        """Test expect() with keyword arguments."""
        mock_child_client.get_new.return_value = sample_activities
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        # Should not raise
        await client.expect(type=ActivityTypes.message, text="Hello!")


# =============================================================================
# Integration-like Tests
# =============================================================================

class TestConversationClientIntegration:
    """Integration-style tests for ConversationClient."""

    @pytest.mark.asyncio
    async def test_conversation_flow(self, mock_agent_client, mock_child_client, sample_activities):
        """Test a typical conversation flow."""
        mock_child_client.send.return_value = sample_activities
        mock_child_client.get_new.return_value = sample_activities
        
        client = ConversationClient(mock_agent_client, timeout=5.0)
        
        # Send a message
        responses = await client.say("Hello")
        assert len(responses) == 2
        
        # Wait for specific activity
        result = await client.wait_for(type=ActivityTypes.message)
        assert result == sample_activities

    @pytest.mark.asyncio
    async def test_timeout_can_be_changed_mid_conversation(self, mock_agent_client, mock_child_client, sample_activities):
        """Test that timeout can be changed during a conversation."""
        mock_child_client.send.return_value = sample_activities
        
        client = ConversationClient(mock_agent_client, timeout=1.0)
        
        await client.say("First message")
        mock_child_client.send.assert_called_with("First message", wait=None, timeout=1.0)
        
        # Change timeout
        client.timeout = 10.0
        
        await client.say("Second message")
        mock_child_client.send.assert_called_with("Second message", wait=None, timeout=10.0)

    @pytest.mark.asyncio
    async def test_expect_replies_mode(self, mock_agent_client, mock_child_client, sample_activities):
        """Test conversation in expect_replies mode."""
        mock_child_client.send_expect_replies.return_value = sample_activities
        
        client = ConversationClient(mock_agent_client, expect_replies=True, timeout=5.0)
        
        responses = await client.say("Hello")
        
        mock_child_client.send_expect_replies.assert_called_once()
        mock_child_client.send.assert_not_called()
        assert responses == sample_activities