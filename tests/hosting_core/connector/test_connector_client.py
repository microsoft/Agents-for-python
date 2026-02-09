# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for ConversationsOperations.send_to_conversation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientSession, ClientResponse

from microsoft_agents.activity import Activity, ResourceResponse
from microsoft_agents.hosting.core.connector.client.connector_client import (
    ConversationsOperations,
)


class TestSendToConversation:
    """Tests for ConversationsOperations.send_to_conversation."""

    @pytest.fixture
    def mock_response(self):
        """Creates a configurable mock ClientResponse."""

        def _make_response(status=200, content_length=None, body=b""):
            resp = AsyncMock(spec=ClientResponse)
            resp.status = status
            resp.content_length = content_length
            resp.content = AsyncMock()
            resp.content.read = AsyncMock(return_value=body)
            resp.raise_for_status = MagicMock()
            # Support async context manager (async with client.post(...) as response)
            return resp

        return _make_response

    @pytest.fixture
    def mock_client(self, mock_response):
        """Creates a mock ClientSession with a configurable post method."""
        client = MagicMock(spec=ClientSession)

        def _configure(response):
            ctx = AsyncMock()
            ctx.__aenter__ = AsyncMock(return_value=response)
            ctx.__aexit__ = AsyncMock(return_value=False)
            client.post = MagicMock(return_value=ctx)
            return client

        return _configure

    @pytest.fixture
    def activity(self):
        return Activity(type="message", text="Hello, world!")

    @pytest.mark.asyncio
    async def test_send_to_conversation_success_with_content(
        self, mock_client, mock_response, activity
    ):
        """Should return ResourceResponse validated from decoded response body."""
        response = mock_response(
            status=200,
            content_length=22,
            body=b'{"id": "activity-id-123"}',
        )
        client = mock_client(response)
        ops = ConversationsOperations(client)

        result = await ops.send_to_conversation("conv-1", activity)

        assert isinstance(result, ResourceResponse)
        assert result.id == "activity-id-123"
        client.post.assert_called_once()
        call_args = client.post.call_args
        assert call_args[0][0] == "v3/conversations/conv-1/activities"

    @pytest.mark.asyncio
    async def test_send_to_conversation_success_no_content(
        self, mock_client, mock_response, activity
    ):
        """Should return empty ResourceResponse when no content."""
        response = mock_response(status=200, content_length=None, body=b"")
        client = mock_client(response)
        ops = ConversationsOperations(client)

        result = await ops.send_to_conversation("conv-1", activity)

        assert isinstance(result, ResourceResponse)
        assert result.id is None


class TestReplyToActivity:
    """Tests for ConversationsOperations.reply_to_activity."""

    @pytest.fixture
    def mock_response(self):
        def _make_response(status=200, content_length=None, body=b""):
            resp = AsyncMock(spec=ClientResponse)
            resp.status = status
            resp.content_length = content_length
            resp.content = AsyncMock()
            resp.content.read = AsyncMock(return_value=body)
            resp.raise_for_status = MagicMock()
            return resp

        return _make_response

    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=ClientSession)

        def _configure(response):
            ctx = AsyncMock()
            ctx.__aenter__ = AsyncMock(return_value=response)
            ctx.__aexit__ = AsyncMock(return_value=False)
            client.post = MagicMock(return_value=ctx)
            return client

        return _configure

    @pytest.fixture
    def activity(self):
        return Activity(type="message", text="Hello, world!")

    @pytest.mark.asyncio
    async def test_reply_to_activity_success_with_content(
        self, mock_client, mock_response, activity
    ):
        """Should return ResourceResponse parsed from JSON response body."""
        json_body = b'{"id": "reply-id-456"}'
        response = mock_response(
            status=200, content_length=len(json_body), body=json_body
        )
        client = mock_client(response)
        ops = ConversationsOperations(client)

        result = await ops.reply_to_activity("conv-1", "act-1", activity)

        assert isinstance(result, ResourceResponse)
        assert result.id == "reply-id-456"
        call_args = client.post.call_args
        assert call_args[0][0] == "v3/conversations/conv-1/activities/act-1"

    @pytest.mark.asyncio
    async def test_reply_to_activity_success_no_content(
        self, mock_client, mock_response, activity
    ):
        """Should return empty ResourceResponse when no content is returned."""
        response = mock_response(status=200, content_length=None, body=b"")
        client = mock_client(response)
        ops = ConversationsOperations(client)

        result = await ops.reply_to_activity("conv-1", "act-1", activity)

        assert isinstance(result, ResourceResponse)
        assert result.id is None or result.id == ""
