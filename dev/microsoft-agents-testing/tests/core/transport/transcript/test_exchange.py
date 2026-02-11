# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Exchange class."""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import aiohttp

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)
from microsoft_agents.testing.core.transport.transcript import Exchange


class TestExchange:
    """Tests for the Exchange model."""

    def test_exchange_default_initialization(self):
        """Exchange should initialize with default values."""
        exchange = Exchange()
        
        assert exchange.request is None
        assert exchange.request_at is None
        assert exchange.status_code is None
        assert exchange.body is None
        assert exchange.invoke_response is None
        assert exchange.error is None
        assert exchange.responses == []
        assert exchange.response_at is None

    def test_exchange_with_request(self):
        """Exchange should store the request activity."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        exchange = Exchange(request=activity)
        
        assert exchange.request == activity
        assert exchange.request.text == "Hello"
        assert exchange.request.type == ActivityTypes.message

    def test_exchange_with_responses(self):
        """Exchange should store response activities."""
        request = Activity(type=ActivityTypes.message, text="Hello")
        response1 = Activity(type=ActivityTypes.message, text="Response 1")
        response2 = Activity(type=ActivityTypes.message, text="Response 2")
        
        exchange = Exchange(
            request=request,
            responses=[response1, response2]
        )
        
        assert len(exchange.responses) == 2
        assert exchange.responses[0].text == "Response 1"
        assert exchange.responses[1].text == "Response 2"

    def test_exchange_with_status_code_and_body(self):
        """Exchange should store HTTP response metadata."""
        exchange = Exchange(
            status_code=200,
            body='{"result": "success"}'
        )
        
        assert exchange.status_code == 200
        assert exchange.body == '{"result": "success"}'

    def test_exchange_with_error(self):
        """Exchange should store error information."""
        exchange = Exchange(error="Connection timeout")
        
        assert exchange.error == "Connection timeout"

    def test_exchange_with_invoke_response(self):
        """Exchange should store invoke response."""
        invoke_resp = InvokeResponse(status=200, body={"key": "value"})
        exchange = Exchange(invoke_response=invoke_resp)
        
        assert exchange.invoke_response == invoke_resp
        assert exchange.invoke_response.status == 200


class TestExchangeLatency:
    """Tests for Exchange latency calculations."""

    def test_latency_with_both_timestamps(self):
        """Latency should be calculated when both timestamps are present."""
        request_time = datetime(2026, 1, 30, 10, 0, 0)
        response_time = datetime(2026, 1, 30, 10, 0, 1)  # 1 second later
        
        exchange = Exchange(
            request_at=request_time,
            response_at=response_time
        )
        
        latency = exchange.latency
        assert latency is not None
        assert latency == timedelta(seconds=1)

    def test_latency_ms_with_both_timestamps(self):
        """Latency in milliseconds should be calculated correctly."""
        request_time = datetime(2026, 1, 30, 10, 0, 0)
        response_time = datetime(2026, 1, 30, 10, 0, 0, 500000)  # 500ms later
        
        exchange = Exchange(
            request_at=request_time,
            response_at=response_time
        )
        
        latency_ms = exchange.latency_ms
        assert latency_ms is not None
        assert latency_ms == 500.0

    def test_latency_without_request_timestamp(self):
        """Latency should be None when request_at is missing."""
        exchange = Exchange(response_at=datetime.now())
        
        assert exchange.latency is None
        assert exchange.latency_ms is None

    def test_latency_without_response_timestamp(self):
        """Latency should be None when response_at is missing."""
        exchange = Exchange(request_at=datetime.now())
        
        assert exchange.latency is None
        assert exchange.latency_ms is None

    def test_latency_without_any_timestamps(self):
        """Latency should be None when both timestamps are missing."""
        exchange = Exchange()
        
        assert exchange.latency is None
        assert exchange.latency_ms is None


class TestExchangeIsAllowedException:
    """Tests for is_allowed_exception static method."""

    def test_client_timeout_is_allowed(self):
        """ClientTimeout should be an allowed exception."""
        exception = aiohttp.ClientTimeout()
        assert Exchange.is_allowed_exception(exception) is True

    def test_client_connection_error_is_allowed(self):
        """ClientConnectionError should be an allowed exception."""
        exception = aiohttp.ClientConnectionError("Connection failed")
        assert Exchange.is_allowed_exception(exception) is True

    def test_value_error_is_not_allowed(self):
        """ValueError should not be an allowed exception."""
        exception = ValueError("Invalid value")
        assert Exchange.is_allowed_exception(exception) is False

    def test_runtime_error_is_not_allowed(self):
        """RuntimeError should not be an allowed exception."""
        exception = RuntimeError("Runtime error")
        assert Exchange.is_allowed_exception(exception) is False

    def test_generic_exception_is_not_allowed(self):
        """Generic Exception should not be an allowed exception."""
        exception = Exception("Generic error")
        assert Exchange.is_allowed_exception(exception) is False


class TestExchangeFromRequest:
    """Tests for the from_request async static method."""

    class _AsyncBytesIterator:
        def __init__(self, chunks: list[bytes]):
            self._chunks = chunks
            self._idx = 0

        def __aiter__(self):
            return self

        async def __anext__(self) -> bytes:
            if self._idx >= len(self._chunks):
                raise StopAsyncIteration
            chunk = self._chunks[self._idx]
            self._idx += 1
            return chunk

    @staticmethod
    def _create_mock_response(status: int = 200, text: str = "OK", content=None):
        """Create a mock response that passes isinstance check without spec side effects."""
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.text = AsyncMock(return_value=text)
        mock_response.content = content
        # Make it pass isinstance check for aiohttp.ClientResponse
        mock_response.__class__ = aiohttp.ClientResponse
        return mock_response

    @pytest.mark.asyncio
    async def test_from_request_with_allowed_exception(self):
        """from_request should handle allowed exceptions."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        exception = aiohttp.ClientConnectionError("Connection failed")
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=exception
        )
        
        assert exchange.request == activity
        assert exchange.error == "Connection failed"
        assert exchange.status_code is None
        assert exchange.responses == []

    @pytest.mark.asyncio
    async def test_from_request_with_timeout_exception(self):
        """from_request should handle timeout exceptions."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        exception = aiohttp.ConnectionTimeoutError()
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=exception
        )
        
        assert exchange.request == activity
        assert exchange.error is not None

    @pytest.mark.asyncio
    async def test_from_request_with_disallowed_exception_raises(self):
        """from_request should re-raise disallowed exceptions."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        exception = ValueError("Invalid value")
        
        with pytest.raises(ValueError, match="Invalid value"):
            await Exchange.from_request(
                request_activity=activity,
                response_or_exception=exception
            )

    @pytest.mark.asyncio
    async def test_from_request_with_expect_replies_response(self):
        """from_request should parse expect_replies response."""
        activity = Activity(
            type=ActivityTypes.message,
            text="Hello",
            delivery_mode=DeliveryModes.expect_replies
        )
        
        # Mock aiohttp response
        mock_response = self._create_mock_response(
            status=200,
            text=json.dumps({"activities": [
                {"type": "message", "text": "Reply 1"},
                {"type": "message", "text": "Reply 2"}
            ]})
        )
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=mock_response
        )
        
        assert exchange.request == activity
        assert exchange.status_code == 200
        assert len(exchange.responses) == 2
        assert exchange.responses[0].text == "Reply 1"
        assert exchange.responses[1].text == "Reply 2"

    @pytest.mark.asyncio
    async def test_from_request_with_stream_delivery_parses_activity_events(self):
        """from_request should parse stream delivery mode SSE events."""
        activity = Activity(
            type=ActivityTypes.message,
            text="Hello",
            delivery_mode=DeliveryModes.stream,
        )

        # Mock aiohttp response with SSE-like payload (event: activity + data: <activity json>)
        mock_response = self._create_mock_response(
            status=200,
            content=self._AsyncBytesIterator([
                b"event: activity\n",
                b"data: {\"type\": \"message\", \"text\": \"Stream reply 1\"}\n",
                b"event: activity\n",
                b"data: {\"type\": \"message\", \"text\": \"Stream reply 2\"}\n",
            ])
        )

        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=mock_response,
        )

        assert exchange.request == activity
        assert exchange.status_code == 200
        assert [a.text for a in exchange.responses] == ["Stream reply 1", "Stream reply 2"]

    @pytest.mark.asyncio
    async def test_from_request_with_invoke_response(self):
        """from_request should parse invoke response."""
        activity = Activity(
            type=ActivityTypes.invoke,
            name="testInvoke"
        )
        
        # Mock aiohttp response
        mock_response = self._create_mock_response(
            status=200,
            text=json.dumps({"result": "success"})
        )
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=mock_response
        )
        
        assert exchange.request == activity
        assert exchange.status_code == 200
        assert exchange.invoke_response is not None
        assert exchange.invoke_response.status == 200
        assert exchange.invoke_response.body == {"result": "success"}

    @pytest.mark.asyncio
    async def test_from_request_with_regular_message_response(self):
        """from_request should handle regular message response."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        # Mock aiohttp response
        mock_response = self._create_mock_response(status=200, text="OK")
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=mock_response
        )
        
        assert exchange.request == activity
        assert exchange.status_code == 200
        assert exchange.body == "OK"
        assert exchange.responses == []
        assert exchange.invoke_response is None

    @pytest.mark.asyncio
    async def test_from_request_with_kwargs(self):
        """from_request should pass through additional kwargs."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        request_time = datetime(2026, 1, 30, 10, 0, 0)
        
        mock_response = self._create_mock_response(status=200, text="OK")
        
        exchange = await Exchange.from_request(
            request_activity=activity,
            response_or_exception=mock_response,
            request_at=request_time
        )
        
        assert exchange.request_at == request_time

    @pytest.mark.asyncio
    async def test_from_request_with_invalid_type_raises(self):
        """from_request should raise for invalid response types."""
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        with pytest.raises(ValueError, match="must be an Exception or aiohttp.ClientResponse"):
            await Exchange.from_request(
                request_activity=activity,
                response_or_exception="invalid_type"  # type: ignore
            )
