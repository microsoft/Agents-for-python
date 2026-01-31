# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the AiohttpSender class."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import pytest
import aiohttp
from aiohttp import ClientSession, ClientResponse

from microsoft_agents.activity import Activity, ActivityTypes, DeliveryModes
from microsoft_agents.testing.core.transport import AiohttpSender
from microsoft_agents.testing.core.transport.transcript import Transcript, Exchange


def create_mock_response(status: int = 200, text: str = "OK"):
    """Create a mock aiohttp.ClientResponse that passes isinstance checks."""
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=text)
    return mock_response


def create_mock_session(mock_response):
    """Create a mock session with async context manager support."""
    mock_session = MagicMock(spec=ClientSession)
    
    @asynccontextmanager
    async def mock_post(*args, **kwargs):
        yield mock_response
    
    mock_session.post = mock_post
    return mock_session


class TestAiohttpSenderInitialization:
    """Tests for AiohttpSender initialization."""

    def test_aiohttp_sender_stores_session(self):
        """AiohttpSender should store the provided session."""
        mock_session = MagicMock(spec=ClientSession)
        
        sender = AiohttpSender(session=mock_session)
        
        assert sender._session is mock_session


class TestAiohttpSenderSend:
    """Tests for AiohttpSender.send method."""

    @pytest.mark.asyncio
    async def test_send_posts_to_api_messages(self):
        """send should POST to api/messages endpoint."""
        mock_response = create_mock_response(200, "OK")
        
        mock_session = MagicMock(spec=ClientSession)
        post_calls = []
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            post_calls.append((args, kwargs))
            yield mock_response
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        await sender.send(activity)
        
        assert len(post_calls) == 1
        assert post_calls[0][0][0] == "api/messages"

    @pytest.mark.asyncio
    async def test_send_serializes_activity_correctly(self):
        """send should serialize activity with correct options."""
        mock_response = create_mock_response(200, "OK")
        
        mock_session = MagicMock(spec=ClientSession)
        post_calls = []
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            post_calls.append((args, kwargs))
            yield mock_response
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        await sender.send(activity)
        
        json_data = post_calls[0][1]["json"]
        
        # Should include the activity data
        assert json_data["type"] == "message"
        assert json_data["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_returns_exchange(self):
        """send should return an Exchange object."""
        mock_response = create_mock_response(200, "OK")
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        exchange = await sender.send(activity)
        
        assert isinstance(exchange, Exchange)
        assert exchange.request == activity
        assert exchange.status_code == 200

    @pytest.mark.asyncio
    async def test_send_records_timestamps(self):
        """send should record request and response timestamps."""
        mock_response = create_mock_response(200, "OK")
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        exchange = await sender.send(activity)
        
        assert exchange.request_at is not None
        assert exchange.response_at is not None
        assert isinstance(exchange.request_at, datetime)
        assert isinstance(exchange.response_at, datetime)

    @pytest.mark.asyncio
    async def test_send_records_to_transcript(self):
        """send should record exchange to provided transcript."""
        mock_response = create_mock_response(200, "OK")
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        transcript = Transcript()
        
        await sender.send(activity, transcript=transcript)
        
        assert len(transcript.history()) == 1
        assert transcript.history()[0].request.text == "Hello"

    @pytest.mark.asyncio
    async def test_send_without_transcript_does_not_record(self):
        """send without transcript should not raise."""
        mock_response = create_mock_response(200, "OK")
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        # Should not raise
        exchange = await sender.send(activity)
        assert exchange is not None

    @pytest.mark.asyncio
    async def test_send_passes_kwargs(self):
        """send should pass additional kwargs to the session.post call."""
        mock_response = create_mock_response(200, "OK")
        
        mock_session = MagicMock(spec=ClientSession)
        post_calls = []
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            post_calls.append((args, kwargs))
            yield mock_response
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        await sender.send(activity, timeout=30)
        
        assert post_calls[0][1].get("timeout") == 30


class TestAiohttpSenderErrorHandling:
    """Tests for AiohttpSender error handling."""

    @pytest.mark.asyncio
    async def test_send_handles_connection_error(self):
        """send should handle connection errors gracefully."""
        mock_session = MagicMock(spec=ClientSession)
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            raise aiohttp.ClientConnectionError("Connection failed")
            yield  # Never reached, but needed for generator
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        exchange = await sender.send(activity)
        
        assert exchange.error is not None
        assert "Connection failed" in exchange.error

    @pytest.mark.asyncio
    async def test_send_handles_timeout_error(self):
        """send should handle timeout errors gracefully."""
        mock_session = MagicMock(spec=ClientSession)
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            raise aiohttp.ServerTimeoutError("Timeout")
            yield  # Never reached, but needed for generator
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        exchange = await sender.send(activity)
        
        assert exchange.error is not None

    @pytest.mark.asyncio
    async def test_send_records_error_to_transcript(self):
        """send should record error exchanges to transcript."""
        mock_session = MagicMock(spec=ClientSession)
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            raise aiohttp.ClientConnectionError("Connection failed")
            yield  # Never reached
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        transcript = Transcript()
        
        await sender.send(activity, transcript=transcript)
        
        assert len(transcript.history()) == 1
        assert transcript.history()[0].error is not None

    @pytest.mark.asyncio
    async def test_send_raises_unexpected_errors(self):
        """send should re-raise unexpected errors."""
        mock_session = MagicMock(spec=ClientSession)
        
        @asynccontextmanager
        async def mock_post(*args, **kwargs):
            raise ValueError("Unexpected error")
            yield  # Never reached
        
        mock_session.post = mock_post
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        with pytest.raises(ValueError, match="Unexpected error"):
            await sender.send(activity)


class TestAiohttpSenderExpectReplies:
    """Tests for AiohttpSender with expect_replies delivery mode."""

    @pytest.mark.asyncio
    async def test_send_expect_replies_parses_responses(self):
        """send with expect_replies should parse inline responses."""
        responses_json = json.dumps([
            {"type": "message", "text": "Reply 1"},
            {"type": "message", "text": "Reply 2"}
        ])
        
        mock_response = create_mock_response(200, responses_json)
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(
            type=ActivityTypes.message,
            text="Hello",
            delivery_mode=DeliveryModes.expect_replies
        )
        
        exchange = await sender.send(activity)
        
        assert len(exchange.responses) == 2
        assert exchange.responses[0].text == "Reply 1"
        assert exchange.responses[1].text == "Reply 2"


class TestAiohttpSenderInvoke:
    """Tests for AiohttpSender with invoke activities."""

    @pytest.mark.asyncio
    async def test_send_invoke_parses_invoke_response(self):
        """send with invoke activity should parse invoke response."""
        invoke_response_json = json.dumps({"result": "success"})
        
        mock_response = create_mock_response(200, invoke_response_json)
        mock_session = create_mock_session(mock_response)
        
        sender = AiohttpSender(session=mock_session)
        activity = Activity(
            type=ActivityTypes.invoke,
            name="testAction"
        )
        
        exchange = await sender.send(activity)
        
        assert exchange.invoke_response is not None
        assert exchange.invoke_response.status == 200
        assert exchange.invoke_response.body == {"result": "success"}
