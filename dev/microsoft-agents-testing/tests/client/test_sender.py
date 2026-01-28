"""
Unit tests for the Sender classes.

This module tests:
- Sender abstract class
- AiohttpSender implementation
- Successful request handling
- Exception handling
- Transcript recording
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from microsoft_agents.testing.transcript import Exchange, Transcript
from microsoft_agents.testing.client import Sender, AiohttpSender
from microsoft_agents.activity import Activity, ActivityTypes


# =============================================================================
# Sender Abstract Class Tests
# =============================================================================

class TestSenderAbstract:
    """Test Sender abstract class."""
    
    def test_sender_is_abstract(self):
        """Verify Sender cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Sender()
    
    def test_sender_subclass_must_implement_send(self):
        """Verify subclass must implement send method."""
        class IncompleteSender(Sender):
            pass
        
        with pytest.raises(TypeError):
            IncompleteSender()
    
    def test_sender_subclass_with_send_implementation(self):
        """Verify subclass with send method can be instantiated."""
        class CompleteSender(Sender):
            async def send(self, activity, transcript=None, **kwargs):
                return Exchange()
        
        sender = CompleteSender()
        assert sender is not None


# =============================================================================
# AiohttpSender Initialization Tests
# =============================================================================

class TestAiohttpSenderInit:
    """Test AiohttpSender initialization."""
    
    def test_init_with_session(self):
        """Test initialization with a ClientSession."""
        mock_session = MagicMock(spec=aiohttp.ClientSession)
        sender = AiohttpSender(mock_session)
        
        assert sender._session is mock_session


# =============================================================================
# AiohttpSender Send Tests
# =============================================================================

class TestAiohttpSenderSend:
    """Test AiohttpSender.send() method."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp ClientSession."""
        return MagicMock(spec=aiohttp.ClientSession)
    
    @pytest.fixture
    def sample_activity(self):
        """Create a sample Activity for testing."""
        return Activity(type=ActivityTypes.message, text="Hello, World!")
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock aiohttp response."""
        response = AsyncMock(spec=aiohttp.ClientResponse)
        response.status = 200
        response.text = AsyncMock(return_value='[]')
        return response
    
    @pytest.mark.asyncio
    async def test_send_successful_request(self, mock_session, sample_activity, mock_response):
        """Test successful send request."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "api/messages"
    
    @pytest.mark.asyncio
    async def test_send_with_timeout_kwarg(self, mock_session, sample_activity, mock_response):
        """Test send with timeout parameter."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            await sender.send(sample_activity, timeout=30)
        
        call_args = mock_session.post.call_args
        assert call_args[1].get('timeout') == 30
    
    @pytest.mark.asyncio
    async def test_send_records_to_transcript(self, mock_session, sample_activity, mock_response):
        """Test that exchange is recorded to transcript."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        transcript = Transcript()
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            await sender.send(sample_activity, transcript=transcript)
        
        exchanges = transcript.get_all()
        assert len(exchanges) == 1
    
    @pytest.mark.asyncio
    async def test_send_without_transcript(self, mock_session, sample_activity, mock_response):
        """Test send without transcript doesn't raise."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        assert exchange is not None
    
    @pytest.mark.asyncio
    async def test_send_returns_exchange(self, mock_session, sample_activity, mock_response):
        """Test that send returns an Exchange object."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        assert isinstance(exchange, Exchange)


# =============================================================================
# AiohttpSender Exception Handling Tests
# =============================================================================

class TestAiohttpSenderExceptionHandling:
    """Test AiohttpSender exception handling."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp ClientSession."""
        return MagicMock(spec=aiohttp.ClientSession)
    
    @pytest.fixture
    def sample_activity(self):
        """Create a sample Activity for testing."""
        return Activity(type=ActivityTypes.message, text="Hello, World!")
    
    @pytest.mark.asyncio
    async def test_send_handles_client_timeout(self, mock_session, sample_activity):
        """Test handling of ClientTimeout exception."""
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = aiohttp.ClientTimeout()
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, error="Timeout")
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        mock_from_request.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_handles_connection_error(self, mock_session, sample_activity):
        """Test handling of ClientConnectionError exception."""
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = aiohttp.ClientConnectionError("Connection failed")
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, error="Connection failed")
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        mock_from_request.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_handles_generic_exception(self, mock_session, sample_activity):
        """Test handling of generic exceptions."""
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = Exception("Generic error")
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=sample_activity, error="Generic error")
            mock_from_request.return_value = mock_exchange
            
            exchange = await sender.send(sample_activity)
        
        mock_from_request.assert_called()


# =============================================================================
# AiohttpSender Activity Serialization Tests
# =============================================================================

class TestAiohttpSenderActivitySerialization:
    """Test that activities are serialized correctly."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp ClientSession."""
        return MagicMock(spec=aiohttp.ClientSession)
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock aiohttp response."""
        response = AsyncMock(spec=aiohttp.ClientResponse)
        response.status = 200
        response.text = AsyncMock(return_value='[]')
        return response
    
    @pytest.mark.asyncio
    async def test_activity_serialized_with_correct_options(self, mock_session, mock_response):
        """Test that activity is serialized with correct model_dump options."""
        activity = Activity(type=ActivityTypes.message, text="Test")
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        with patch.object(Exchange, 'from_request', new_callable=AsyncMock) as mock_from_request:
            mock_exchange = Exchange(request=activity, status_code=200)
            mock_from_request.return_value = mock_exchange
            
            await sender.send(activity)
        
        call_args = mock_session.post.call_args
        json_data = call_args[1].get('json')
        assert json_data is not None
        assert 'type' in json_data
        assert json_data['type'] == 'message'


# =============================================================================
# AiohttpSender Timing Tests
# =============================================================================

class TestAiohttpSenderTiming:
    """Test timing capture in send method."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp ClientSession."""
        return MagicMock(spec=aiohttp.ClientSession)
    
    @pytest.fixture
    def sample_activity(self):
        """Create a sample Activity for testing."""
        return Activity(type=ActivityTypes.message, text="Hello!")
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock aiohttp response."""
        response = AsyncMock(spec=aiohttp.ClientResponse)
        response.status = 200
        response.text = AsyncMock(return_value='[]')
        return response
    
    @pytest.mark.asyncio
    async def test_exchange_has_timing_info(self, mock_session, sample_activity, mock_response):
        """Test that exchange captures request/response timing."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        exchange = await sender.send(sample_activity)
        
        assert exchange.request_at is not None
        assert exchange.response_at is not None
    
    @pytest.mark.asyncio
    async def test_request_at_before_response_at(self, mock_session, sample_activity, mock_response):
        """Test that request_at is before response_at."""
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        
        exchange = await sender.send(sample_activity)
        
        if exchange.request_at and exchange.response_at:
            assert exchange.request_at <= exchange.response_at


# =============================================================================
# AiohttpSender Integration-Style Tests
# =============================================================================

class TestAiohttpSenderIntegration:
    """Integration-style tests for AiohttpSender."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp ClientSession."""
        return MagicMock(spec=aiohttp.ClientSession)
    
    @pytest.mark.asyncio
    async def test_full_send_receive_flow(self, mock_session):
        """Test complete send/receive flow."""
        activity = Activity(type=ActivityTypes.message, text="Test message")
        
        mock_response = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='[]')
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        transcript = Transcript()
        
        exchange = await sender.send(activity, transcript=transcript)
        
        assert exchange is not None
        assert len(transcript.get_all()) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_sends_recorded_in_transcript(self, mock_session):
        """Test that multiple sends are recorded in transcript."""
        activity1 = Activity(type=ActivityTypes.message, text="First")
        activity2 = Activity(type=ActivityTypes.message, text="Second")
        
        mock_response = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='[]')
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.post.return_value = mock_context
        
        sender = AiohttpSender(mock_session)
        transcript = Transcript()
        
        await sender.send(activity1, transcript=transcript)
        await sender.send(activity2, transcript=transcript)
        
        assert len(transcript.get_all()) == 2