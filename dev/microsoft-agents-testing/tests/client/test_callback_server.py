"""
Unit tests for the CallbackServer classes.

This module tests:
- CallbackServer abstract base class
- AiohttpCallbackServer implementation
"""

import pytest
from unittest.mock import AsyncMock, patch

from microsoft_agents.testing.client import AiohttpCallbackServer
from microsoft_agents.testing.transcript import Transcript, Exchange


# =============================================================================
# AiohttpCallbackServer Initialization Tests
# =============================================================================

class TestAiohttpCallbackServerInit:
    """Test AiohttpCallbackServer initialization."""
    
    def test_init_with_default_port(self):
        server = AiohttpCallbackServer()
        assert server._port == 9873
    
    def test_init_with_custom_port(self):
        server = AiohttpCallbackServer(port=8080)
        assert server._port == 8080
    
    def test_init_creates_app(self):
        server = AiohttpCallbackServer()
        assert server._app is not None
    
    def test_init_transcript_is_none(self):
        server = AiohttpCallbackServer()
        assert server._transcript is None


# =============================================================================
# Service Endpoint Tests
# =============================================================================

class TestServiceEndpoint:
    """Test the service_endpoint property."""
    
    def test_service_endpoint_default_port(self):
        server = AiohttpCallbackServer()
        assert server.service_endpoint == "http://localhost:9873/v3/conversations/"
    
    def test_service_endpoint_custom_port(self):
        server = AiohttpCallbackServer(port=5000)
        assert server.service_endpoint == "http://localhost:5000/v3/conversations/"


# =============================================================================
# Listen Context Manager Tests
# =============================================================================

class TestAiohttpCallbackServerListen:
    """Test the listen context manager."""
    
    @pytest.mark.asyncio
    async def test_listen_creates_transcript_if_none(self):
        server = AiohttpCallbackServer()
        
        with patch('microsoft_agents.testing.client.callback_server.TestServer') as MockTestServer:
            mock_test_server = AsyncMock()
            mock_test_server.__aenter__ = AsyncMock(return_value=mock_test_server)
            mock_test_server.__aexit__ = AsyncMock(return_value=None)
            MockTestServer.return_value = mock_test_server
            
            async with server.listen() as transcript:
                assert transcript is not None
                assert isinstance(transcript, Transcript)
    
    @pytest.mark.asyncio
    async def test_listen_uses_provided_transcript(self):
        server = AiohttpCallbackServer()
        custom_transcript = Transcript()
        
        with patch('microsoft_agents.testing.client.callback_server.TestServer') as MockTestServer:
            mock_test_server = AsyncMock()
            mock_test_server.__aenter__ = AsyncMock(return_value=mock_test_server)
            mock_test_server.__aexit__ = AsyncMock(return_value=None)
            MockTestServer.return_value = mock_test_server
            
            async with server.listen(transcript=custom_transcript) as transcript:
                assert transcript is custom_transcript
    
    @pytest.mark.asyncio
    async def test_listen_clears_transcript_after_exit(self):
        server = AiohttpCallbackServer()
        
        with patch('microsoft_agents.testing.client.callback_server.TestServer') as MockTestServer:
            mock_test_server = AsyncMock()
            mock_test_server.__aenter__ = AsyncMock(return_value=mock_test_server)
            mock_test_server.__aexit__ = AsyncMock(return_value=None)
            MockTestServer.return_value = mock_test_server
            
            async with server.listen():
                assert server._transcript is not None
            
            assert server._transcript is None
    
    @pytest.mark.asyncio
    async def test_listen_raises_if_already_listening(self):
        server = AiohttpCallbackServer()
        
        with patch('microsoft_agents.testing.client.callback_server.TestServer') as MockTestServer:
            mock_test_server = AsyncMock()
            mock_test_server.__aenter__ = AsyncMock(return_value=mock_test_server)
            mock_test_server.__aexit__ = AsyncMock(return_value=None)
            MockTestServer.return_value = mock_test_server
            
            async with server.listen():
                with pytest.raises(RuntimeError, match="already listening"):
                    async with server.listen():
                        pass


# =============================================================================
# Handle Request Tests
# =============================================================================

class TestHandleRequest:
    """Test the _handle_request method."""
    
    @pytest.mark.asyncio
    async def test_handle_request_parses_activity(self):
        server = AiohttpCallbackServer()
        server._transcript = Transcript()
        
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={
            "type": "message",
            "text": "hello"
        })
        
        response = await server._handle_request(mock_request)
        
        assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_handle_request_records_exchange(self):
        server = AiohttpCallbackServer()
        server._transcript = Transcript()
        
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={
            "type": "message",
            "text": "hello"
        })
        
        await server._handle_request(mock_request)
        
        all_exchanges = server._transcript.get_all()
        assert len(all_exchanges) == 1
        assert len(all_exchanges[0].responses) == 1
        assert all_exchanges[0].responses[0].text == "hello"
    
    @pytest.mark.asyncio
    async def test_handle_request_returns_200(self):
        server = AiohttpCallbackServer()
        server._transcript = Transcript()
        
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={
            "type": "message",
            "text": "test"
        })
        
        response = await server._handle_request(mock_request)
        
        assert response.status == 200
        assert response.content_type == "application/json"
    
    @pytest.mark.asyncio
    async def test_handle_request_handles_allowed_exception(self):
        server = AiohttpCallbackServer()
        server._transcript = Transcript()
        
        # Mock allowed exception
        import aiohttp
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(side_effect=aiohttp.ClientConnectionError("test"))
        
        # Patch is_allowed_exception to return True
        with patch.object(Exchange, 'is_allowed_exception', return_value=True):
            response = await server._handle_request(mock_request)
        
        assert response.status == 500


# =============================================================================
# Route Configuration Tests
# =============================================================================

class TestRouteConfiguration:
    """Test that routes are configured correctly."""
    
    def test_post_route_configured(self):
        server = AiohttpCallbackServer()
        
        # Check that the route is configured
        routes = list(server._app.router.routes())
        assert len(routes) > 0
        
        # Find POST route
        post_routes = [r for r in routes if r.method == 'POST']
        assert len(post_routes) > 0
