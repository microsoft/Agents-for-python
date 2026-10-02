# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for MCSConnectorClient User-Agent header behavior."""

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core.connector.get_product_info import get_product_info
from microsoft_agents.hosting.core.connector.mcs import MCSConnectorClient


class TestMCSConnectorClientUserAgentHeader:
    """Ensures MCSConnectorClient sends a User-Agent header.

    NOTE: Unlike ConnectorClient/TeamsConnectorClient and UserTokenClient,
    MCSConnectorClient does not currently set a custom "agents-sdk-py" User-Agent
    header on its session or outgoing requests, so these tests currently fail.
    """

    @pytest.mark.asyncio
    async def test_sets_user_agent_header(self):
        client = MCSConnectorClient(endpoint="https://example.org/endpoint")
        try:
            assert client._client.headers.get("User-Agent") == get_product_info()
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_sends_user_agent_header_on_request(self):
        captured = {}

        async def handler(request):
            captured["user_agent"] = request.headers.get("User-Agent")
            return web.json_response({"id": "activity-id-123"})

        app = web.Application()
        app.router.add_post("/endpoint", handler)
        server = TestServer(app)
        await server.start_server()
        try:
            endpoint = str(server.make_url("/endpoint"))
            client = MCSConnectorClient(endpoint=endpoint)
            try:
                await client.conversations.send_to_conversation(
                    "conv-1", Activity(type="message", text="hi")
                )
            finally:
                await client.close()
        finally:
            await server.close()

        assert captured["user_agent"] == get_product_info()
