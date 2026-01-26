"""
Unit tests for the Sender classes.

This module tests:
- Sender abstract base class
- AiohttpSender implementation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from microsoft_agents.testing.client.exchange.sender import Sender, AiohttpSender
from microsoft_agents.testing.client.exchange.transcript import Transcript
from microsoft_agents.testing.client.exchange.exchange import Exchange
from microsoft_agents.activity import Activity, ActivityTypes


# =============================================================================
# Mock Helpers
# =============================================================================

def create_mock_response(status: int = 200, json_data: dict = None):
    """Create a mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data or {})
    mock_response.text = AsyncMock(return_value="")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    return mock_response


def create_mock_session(response=None):
    """Create a mock aiohttp ClientSession."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_response = response or create_mock_response()
    mock_session.post = MagicMock(return_value=mock_response)
    return mock_session


# =============================================================================
# Sender Base Class Tests
# =============================================================================

class TestSenderBase:
    """Test the Sender abstract base class."""
    
    def test_sender_is_abstract(self):
        # Cannot instantiate abstract class directly without implementing send
        # But we can test that the class has abstract methods
        assert hasattr(Sender, 'send')
    
    def test_sender_has_transcript_property(self):
        # Create a concrete implementation for testing
        class ConcreteSender(Sender):
            async def send(self, activity: Activity) -> Exchange:
                return Exchange()
        
        sender = ConcreteSender()
        assert hasattr(sender, 'transcript')
        assert isinstance(sender.transcript, Transcript)
    
    def test_sender_init_creates_transcript(self):
        class ConcreteSender(Sender):
            async def send(self, activity: Activity) -> Exchange:
                return Exchange()
        
        sender = ConcreteSender()
        assert sender._transcript is not None
    
    def test_sender_init_with_custom_transcript(self):
        class ConcreteSender(Sender):
            async def send(self, activity: Activity) -> Exchange:
                return Exchange()
        
        custom_transcript = Transcript()
        sender = ConcreteSender(transcript=custom_transcript)
        assert sender._transcript is custom_transcript


# =============================================================================
# AiohttpSender Initialization Tests
# =============================================================================

class TestAiohttpSenderInit:
    """Test AiohttpSender initialization."""
    
    def test_init_with_session(self):
        mock_session = create_mock_session()
        sender = AiohttpSender(session=mock_session)
        
        assert sender._session is mock_session
    
    def test_init_creates_default_transcript(self):
        mock_session = create_mock_session()
        sender = AiohttpSender(session=mock_session)
        
        assert isinstance(sender.transcript, Transcript)
    
    def test_init_with_custom_transcript(self):
        mock_session = create_mock_session()
        custom_transcript = Transcript()
        sender = AiohttpSender(session=mock_session, transcript=custom_transcript)
        
        assert sender.transcript is custom_transcript


# =============================================================================
# AiohttpSender Send Tests
# =============================================================================

class TestAiohttpSenderSend:
    """Test the AiohttpSender send method."""
    
    @pytest.mark.asyncio
    async def test_send_posts_to_api_messages(self):
        mock_response = create_mock_response(status=200)
        mock_session = create_mock_session(mock_response)
        sender = AiohttpSender(session=mock_session)
        
        activity = Activity(type=ActivityTypes.message, text="hello")
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_from_request.return_value = Exchange()
            await sender.send(activity)
        
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "api/messages"
    
    @pytest.mark.asyncio
    async def test_send_serializes_activity(self):
        mock_response = create_mock_response(status=200)
        mock_session = create_mock_session(mock_response)
        sender = AiohttpSender(session=mock_session)
        
        activity = Activity(type=ActivityTypes.message, text="hello")
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_from_request.return_value = Exchange()
            await sender.send(activity)
        
        call_args = mock_session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["type"] == "message"
        assert json_data["text"] == "hello"
    
    @pytest.mark.asyncio
    async def test_send_records_exchange(self):
        mock_response = create_mock_response(status=200)
        mock_session = create_mock_session(mock_response)
        sender = AiohttpSender(session=mock_session)
        
        activity = Activity(type=ActivityTypes.message, text="hello")
        expected_exchange = Exchange(status_code=200)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_from_request.return_value = expected_exchange
            result = await sender.send(activity)
        
        assert result is expected_exchange
        assert len(sender.transcript.get_all()) == 1
        assert sender.transcript.get_all()[0] is expected_exchange
    
    @pytest.mark.asyncio
    async def test_send_handles_exception(self):
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.post = MagicMock(side_effect=aiohttp.ClientConnectionError("Connection failed"))
        sender = AiohttpSender(session=mock_session)
        
        activity = Activity(type=ActivityTypes.message, text="hello")
        error_exchange = Exchange(error=str(aiohttp.ClientConnectionError("Connection failed")))
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_from_request.return_value = error_exchange
            result = await sender.send(activity)
        
        assert result is error_exchange
        assert len(sender.transcript.get_all()) == 1


# =============================================================================
# Transcript Integration Tests
# =============================================================================

class TestSenderTranscriptIntegration:
    """Test Sender and Transcript integration."""
    
    @pytest.mark.asyncio
    async def test_multiple_sends_recorded_in_order(self):
        mock_response = create_mock_response(status=200)
        mock_session = create_mock_session(mock_response)
        sender = AiohttpSender(session=mock_session)
        
        exchanges = []
        for i in range(3):
            exchange = Exchange(status_code=200)
            exchanges.append(exchange)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_from_request.side_effect = exchanges
            
            for i in range(3):
                activity = Activity(type=ActivityTypes.message, text=f"message_{i}")
                await sender.send(activity)
        
        all_exchanges = sender.transcript.get_all()
        assert len(all_exchanges) == 3
        for i, exchange in enumerate(all_exchanges):
            assert exchange is exchanges[i]
