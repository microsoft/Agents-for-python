# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the AiohttpCallbackServer class."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core.transport import AiohttpCallbackServer
from microsoft_agents.testing.core.transport.transcript import Transcript, Exchange


class TestAiohttpCallbackServerInitialization:
    """Tests for AiohttpCallbackServer initialization."""

    def test_default_port(self):
        """AiohttpCallbackServer should use default port 9378."""
        server = AiohttpCallbackServer()
        
        assert server._port == 9378

    def test_custom_port(self):
        """AiohttpCallbackServer should accept custom port."""
        server = AiohttpCallbackServer(port=8080)
        
        assert server._port == 8080

    def test_service_endpoint_default_port(self):
        """service_endpoint should use the configured port."""
        server = AiohttpCallbackServer()
        
        assert server.service_endpoint == "http://localhost:9378/v3/conversations/"

    def test_service_endpoint_custom_port(self):
        """service_endpoint should use custom port."""
        server = AiohttpCallbackServer(port=8080)
        
        assert server.service_endpoint == "http://localhost:8080/v3/conversations/"

    def test_initial_transcript_is_none(self):
        """Initial transcript should be None."""
        server = AiohttpCallbackServer()
        
        assert server._transcript is None


class TestAiohttpCallbackServerListen:
    """Tests for AiohttpCallbackServer.listen method."""

    @pytest.mark.asyncio
    async def test_listen_yields_transcript(self):
        """listen should yield a Transcript."""
        server = AiohttpCallbackServer(port=19378)
        
        async with server.listen() as transcript:
            assert isinstance(transcript, Transcript)

    @pytest.mark.asyncio
    async def test_listen_uses_provided_transcript(self):
        """listen should use the provided transcript."""
        server = AiohttpCallbackServer(port=19874)
        provided_transcript = Transcript()
        
        async with server.listen(transcript=provided_transcript) as transcript:
            assert transcript is provided_transcript

    @pytest.mark.asyncio
    async def test_listen_creates_new_transcript_if_none(self):
        """listen should create new transcript if none provided."""
        server = AiohttpCallbackServer(port=19875)
        
        async with server.listen() as transcript:
            assert transcript is not None
            assert isinstance(transcript, Transcript)

    @pytest.mark.asyncio
    async def test_listen_resets_transcript_after_exit(self):
        """listen should reset internal transcript after context exit."""
        server = AiohttpCallbackServer(port=19876)
        
        async with server.listen():
            assert server._transcript is not None
        
        assert server._transcript is None

    @pytest.mark.asyncio
    async def test_listen_raises_if_already_listening(self):
        """listen should raise RuntimeError if already listening."""
        server = AiohttpCallbackServer(port=19877)
        
        async with server.listen():
            with pytest.raises(RuntimeError, match="already listening"):
                async with server.listen():
                    pass


class TestAiohttpCallbackServerHandleRequest:
    """Tests for AiohttpCallbackServer request handling."""

    @pytest.mark.asyncio
    async def test_handle_request_records_activity(self):
        """Server should record incoming activities to transcript."""
        server = AiohttpCallbackServer(port=19878)
        
        async with server.listen() as transcript:
            # Create a mock request
            activity = Activity(type=ActivityTypes.message, text="Hello from agent")
            
            # Simulate the request by calling _handle_request directly
            mock_request = AsyncMock()
            mock_request.json = AsyncMock(return_value=activity.model_dump(by_alias=True, exclude_none=True))
            
            response = await server._handle_request(mock_request)
            
            assert response.status == 200
            assert len(transcript.history()) == 1

    @pytest.mark.asyncio
    async def test_handle_request_parses_activity(self):
        """Server should parse incoming JSON as Activity."""
        server = AiohttpCallbackServer(port=19879)
        
        async with server.listen() as transcript:
            activity_data = {
                "type": "message",
                "text": "Hello from agent",
                "from": {"id": "agent-id", "name": "Agent"}
            }
            
            mock_request = AsyncMock()
            mock_request.json = AsyncMock(return_value=activity_data)
            
            await server._handle_request(mock_request)
            
            recorded = transcript.history()[0]
            assert len(recorded.responses) == 1
            assert recorded.responses[0].text == "Hello from agent"

    @pytest.mark.asyncio
    async def test_handle_request_returns_200_on_success(self):
        """Server should return 200 on successful request."""
        server = AiohttpCallbackServer(port=19880)
        
        async with server.listen():
            activity_data = {"type": "message", "text": "Hello"}
            
            mock_request = AsyncMock()
            mock_request.json = AsyncMock(return_value=activity_data)
            
            response = await server._handle_request(mock_request)
            
            assert response.status == 200
            assert response.content_type == "application/json"

    @pytest.mark.asyncio
    async def test_handle_request_records_response_timestamp(self):
        """Server should record response timestamp."""
        server = AiohttpCallbackServer(port=19881)
        
        async with server.listen() as transcript:
            activity_data = {"type": "message", "text": "Hello"}
            
            mock_request = AsyncMock()
            mock_request.json = AsyncMock(return_value=activity_data)
            
            await server._handle_request(mock_request)
            
            recorded = transcript.history()[0]
            assert recorded.response_at is not None


class TestAiohttpCallbackServerIntegration:
    """Integration tests for AiohttpCallbackServer."""

    @pytest.mark.asyncio
    async def test_multiple_activities_recorded_in_order(self):
        """Multiple activities should be recorded in order."""
        server = AiohttpCallbackServer(port=19882)
        
        async with server.listen() as transcript:
            for i in range(3):
                activity_data = {"type": "message", "text": f"Message {i}"}
                mock_request = AsyncMock()
                mock_request.json = AsyncMock(return_value=activity_data)
                await server._handle_request(mock_request)
            
            history = transcript.history()
            assert len(history) == 3
            for i, exchange in enumerate(history):
                assert exchange.responses[0].text == f"Message {i}"

    @pytest.mark.asyncio
    async def test_transcript_shared_with_child(self):
        """Recorded exchanges should propagate to parent transcript."""
        server = AiohttpCallbackServer(port=19883)
        parent_transcript = Transcript()
        child_transcript = Transcript(parent=parent_transcript)
        
        async with server.listen(transcript=child_transcript):
            activity_data = {"type": "message", "text": "Hello"}
            mock_request = AsyncMock()
            mock_request.json = AsyncMock(return_value=activity_data)
            await server._handle_request(mock_request)
        
        # Both should have the exchange
        assert len(child_transcript.history()) == 1
        assert len(parent_transcript.history()) == 1
