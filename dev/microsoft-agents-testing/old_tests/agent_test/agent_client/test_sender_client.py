# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession

from microsoft_agents.activity import Activity, ActivityTypes, DeliveryModes, InvokeResponse

from microsoft_agents.testing.agent_test.agent_client.sender_client import SenderClient


class TestSenderClientInit:
    """Test SenderClient initialization."""

    def test_init_sets_client(self):
        mock_session = MagicMock(spec=ClientSession)
        sender = SenderClient(mock_session)
        assert sender._client is mock_session


class TestSenderClientSendInternal:
    """Test SenderClient._send method."""

    @pytest.mark.asyncio
    async def test_send_returns_status_and_content(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="response content")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        status, content = await sender._send(activity)

        assert status == 200
        assert content == "response content"

    @pytest.mark.asyncio
    async def test_send_posts_to_api_messages_endpoint(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        await sender._send(activity)

        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "api/messages"

    @pytest.mark.asyncio
    async def test_send_serializes_activity_correctly(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        await sender._send(activity)

        call_args = mock_session.post.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["type"] == "message"
        assert json_payload["text"] == "hello"

    @pytest.mark.asyncio
    async def test_send_raises_exception_on_error_response(self):
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.ok = False
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        with pytest.raises(Exception, match="Failed to send activity: 500"):
            await sender._send(activity)

    @pytest.mark.asyncio
    async def test_send_raises_exception_on_404_response(self):
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.ok = False
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        with pytest.raises(Exception, match="Failed to send activity: 404"):
            await sender._send(activity)


class TestSenderClientSend:
    """Test SenderClient.send method."""

    @pytest.mark.asyncio
    async def test_send_returns_content_string(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="response body")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        result = await sender.send(activity)

        assert result == "response body"

    @pytest.mark.asyncio
    async def test_send_returns_empty_string_when_no_content(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        result = await sender.send(activity)

        assert result == ""


class TestSenderClientSendExpectReplies:
    """Test SenderClient.send_expect_replies method."""

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_list_of_activities(self):
        response_data = {
            "activities": [
                {"type": "message", "text": "reply 1"},
                {"type": "message", "text": "reply 2"},
            ]
        }
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello", delivery_mode=DeliveryModes.expect_replies)

        result = await sender.send_expect_replies(activity)

        assert len(result) == 2
        assert isinstance(result[0], Activity)
        assert isinstance(result[1], Activity)
        assert result[0].text == "reply 1"
        assert result[1].text == "reply 2"

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_empty_list_when_no_activities(self):
        response_data = {"activities": []}
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello", delivery_mode=DeliveryModes.expect_replies)

        result = await sender.send_expect_replies(activity)

        assert result == []

    @pytest.mark.asyncio
    async def test_send_expect_replies_raises_when_delivery_mode_not_expect_replies(self):
        mock_session = MagicMock(spec=ClientSession)
        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        with pytest.raises(ValueError, match="Activity delivery_mode must be 'expect_replies'"):
            await sender.send_expect_replies(activity)

    @pytest.mark.asyncio
    async def test_send_expect_replies_handles_missing_activities_key(self):
        response_data = {}
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello", delivery_mode=DeliveryModes.expect_replies)

        result = await sender.send_expect_replies(activity)

        assert result == []


class TestSenderClientSendInvoke:
    """Test SenderClient.send_invoke method."""

    @pytest.mark.asyncio
    async def test_send_invoke_returns_invoke_response(self):
        response_data = {"key": "value"}
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")

        result = await sender.send_invoke(activity)

        assert isinstance(result, InvokeResponse)
        assert result.status == 200
        assert result.body == {"key": "value"}

    @pytest.mark.asyncio
    async def test_send_invoke_raises_when_activity_type_not_invoke(self):
        mock_session = MagicMock(spec=ClientSession)
        sender = SenderClient(mock_session)
        activity = Activity(type="message", text="hello")

        with pytest.raises(ValueError, match="Activity type must be 'invoke'"):
            await sender.send_invoke(activity)

    @pytest.mark.asyncio
    async def test_send_invoke_with_empty_body(self):
        response_data = {}
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")

        result = await sender.send_invoke(activity)

        assert isinstance(result, InvokeResponse)
        assert result.status == 200
        assert result.body == {}

    @pytest.mark.asyncio
    async def test_send_invoke_with_complex_body(self):
        response_data = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
        }
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")

        result = await sender.send_invoke(activity)

        assert result.body == response_data

    @pytest.mark.asyncio
    async def test_send_invoke_raises_on_invalid_json(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="not valid json")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock(spec=ClientSession)
        mock_session.post = MagicMock(return_value=mock_response)

        sender = SenderClient(mock_session)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")

        with pytest.raises(json.JSONDecodeError):
            await sender.send_invoke(activity)