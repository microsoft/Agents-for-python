# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for ConversationsOperations using aiohttp TestServer."""

import json

import pytest
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import Activity, ResourceResponse
from microsoft_agents.hosting.core.connector.client.connector_client import (
    ConversationsOperations,
)


def _create_app(routes):
    """Create an aiohttp app with the given route table."""
    app = web.Application()
    app.router.add_routes(routes)
    return app


class TestSendToConversation:
    """Tests for ConversationsOperations.send_to_conversation."""

    @pytest.fixture
    def activity(self):
        return Activity(type="message", text="Hello, world!")

    @pytest.mark.asyncio
    async def test_send_to_conversation_success_with_content(self, activity):
        """Should return ResourceResponse validated from response text."""

        async def handler(request):
            return web.json_response({"id": "activity-id-123"})

        routes = [web.post("/v3/conversations/{conversation_id}/activities", handler)]
        app = _create_app(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                result = await ops.send_to_conversation("conv-1", activity)

            assert isinstance(result, ResourceResponse)
            assert result.id == "activity-id-123"
        finally:
            await server.close()

    @pytest.mark.asyncio
    async def test_send_to_conversation_success_no_content(self, activity):
        """Should return empty ResourceResponse when no content."""

        async def handler(request):
            return web.Response(status=200, text="")

        routes = [web.post("/v3/conversations/{conversation_id}/activities", handler)]
        app = _create_app(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                result = await ops.send_to_conversation("conv-1", activity)

            assert isinstance(result, ResourceResponse)
            assert result.id is None
        finally:
            await server.close()


class TestReplyToActivity:
    """Tests for ConversationsOperations.reply_to_activity."""

    @pytest.fixture
    def activity(self):
        return Activity(type="message", text="Hello, world!")

    @pytest.mark.asyncio
    async def test_reply_to_activity_success_with_content(self, activity):
        """Should return ResourceResponse parsed from JSON response text."""

        async def handler(request):
            return web.json_response({"id": "reply-id-456"})

        routes = [
            web.post(
                "/v3/conversations/{conversation_id}/activities/{activity_id}",
                handler,
            )
        ]
        app = _create_app(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                result = await ops.reply_to_activity("conv-1", "act-1", activity)

            assert isinstance(result, ResourceResponse)
            assert result.id == "reply-id-456"
        finally:
            await server.close()

    @pytest.mark.asyncio
    async def test_reply_to_activity_success_no_content(self, activity):
        """Should return empty ResourceResponse when no content is returned."""

        async def handler(request):
            return web.Response(status=200, text="")

        routes = [
            web.post(
                "/v3/conversations/{conversation_id}/activities/{activity_id}",
                handler,
            )
        ]
        app = _create_app(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                result = await ops.reply_to_activity("conv-1", "act-1", activity)

            assert isinstance(result, ResourceResponse)
            assert result.id is None
        finally:
            await server.close()
