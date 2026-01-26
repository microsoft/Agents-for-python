# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer, TestClient

from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.testing.agent_test.agent_client.response_server import (
    ResponseServer,
)
from microsoft_agents.testing.agent_test.agent_client.response_collector import (
    ResponseCollector,
)


class TestResponseServerInit:
    """Test ResponseServer initialization."""

    def test_init_sets_default_port(self):
        server = ResponseServer()
        assert server._port == 9873

    def test_init_sets_custom_port(self):
        server = ResponseServer(port=8080)
        assert server._port == 8080

    def test_init_collector_is_none(self):
        server = ResponseServer()
        assert server._collector is None

    def test_init_creates_app_with_route(self):
        server = ResponseServer()
        # Verify the app has the expected route registered
        assert server._app is not None
        assert isinstance(server._app, Application)


class TestResponseServerServiceEndpoint:
    """Test ResponseServer.service_endpoint property."""

    def test_service_endpoint_returns_correct_url_default_port(self):
        server = ResponseServer()
        assert server.service_endpoint == "http://localhost:9873/v3/conversations/"

    def test_service_endpoint_returns_correct_url_custom_port(self):
        server = ResponseServer(port=5000)
        assert server.service_endpoint == "http://localhost:5000/v3/conversations/"


class TestResponseServerListen:
    """Test ResponseServer.listen async context manager."""

    @pytest.mark.asyncio
    async def test_listen_yields_response_collector(self):
        server = ResponseServer(port=19871)
        async with server.listen() as collector:
            assert isinstance(collector, ResponseCollector)

    @pytest.mark.asyncio
    async def test_listen_sets_collector_during_context(self):
        server = ResponseServer(port=19872)
        async with server.listen() as collector:
            assert server._collector is collector

    @pytest.mark.asyncio
    async def test_listen_clears_collector_after_context(self):
        server = ResponseServer(port=19873)
        async with server.listen():
            pass
        assert server._collector is None

    @pytest.mark.asyncio
    async def test_listen_raises_when_already_listening(self):
        server = ResponseServer(port=19874)
        async with server.listen():
            with pytest.raises(RuntimeError, match="already listening"):
                async with server.listen():
                    pass


class TestResponseServerHandleRequest:
    """Test ResponseServer._handle_request method."""

    @pytest.mark.asyncio
    async def test_handle_request_returns_200_for_valid_activity(self):
        server = ResponseServer(port=19881)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                activity_data = {
                    "type": "message",
                    "text": "Hello, World!",
                }
                async with session.post(
                    f"{server.service_endpoint}test-conversation/activities",
                    json=activity_data,
                ) as response:
                    assert response.status == 200

    @pytest.mark.asyncio
    async def test_handle_request_collects_activity(self):
        server = ResponseServer(port=19882)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                activity_data = {
                    "type": "message",
                    "text": "Test message",
                }
                async with session.post(
                    f"{server.service_endpoint}test-conversation/activities",
                    json=activity_data,
                ) as response:
                    pass
                activities = collector.get_activities()
                assert len(activities) == 1
                assert activities[0].type == "message"
                assert activities[0].text == "Test message"

    @pytest.mark.asyncio
    async def test_handle_request_returns_json_response(self):
        server = ResponseServer(port=19883)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                activity_data = {"type": "message", "text": "Hello"}
                async with session.post(
                    f"{server.service_endpoint}test/activities",
                    json=activity_data,
                ) as response:
                    response_json = await response.json()
                    assert response_json == {"message": "Activity received"}

    @pytest.mark.asyncio
    async def test_handle_request_returns_500_for_invalid_json(self):
        server = ResponseServer(port=19884)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server.service_endpoint}test/activities",
                    data="invalid json",
                    headers={"Content-Type": "application/json"},
                ) as response:
                    assert response.status == 500

    @pytest.mark.asyncio
    async def test_handle_request_collects_multiple_activities(self):
        server = ResponseServer(port=19885)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                for i in range(3):
                    activity_data = {"type": "message", "text": f"Message {i}"}
                    async with session.post(
                        f"{server.service_endpoint}test/activities",
                        json=activity_data,
                    ) as response:
                        pass
                activities = collector.get_activities()
                assert len(activities) == 3

    @pytest.mark.asyncio
    async def test_handle_request_handles_typing_activity(self):
        server = ResponseServer(port=19886)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                activity_data = {"type": ActivityTypes.typing}
                async with session.post(
                    f"{server.service_endpoint}test/activities",
                    json=activity_data,
                ) as response:
                    assert response.status == 200
                activities = collector.get_activities()
                assert len(activities) == 1
                assert activities[0].type == ActivityTypes.typing

    @pytest.mark.asyncio
    async def test_handle_request_handles_various_conversation_paths(self):
        server = ResponseServer(port=19887)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                paths = [
                    "conv1/activities",
                    "conv2/activities/reply",
                    "conv3/members",
                ]
                for path in paths:
                    activity_data = {"type": "message", "text": path}
                    async with session.post(
                        f"{server.service_endpoint}{path}",
                        json=activity_data,
                    ) as response:
                        assert response.status == 200
                activities = collector.get_activities()
                assert len(activities) == 3


class TestResponseServerHandleRequestWithTestServer:
    """Test ResponseServer._handle_request using aiohttp TestServer/TestClient."""

    @pytest.mark.asyncio
    async def test_handle_request_with_test_client(self):
        server = ResponseServer()
        server._collector = ResponseCollector()
        
        async with TestServer(server._app) as test_server:
            async with TestClient(test_server) as client:
                activity_data = {"type": "message", "text": "Hello"}
                response = await client.post(
                    "/v3/conversations/test/activities",
                    json=activity_data,
                )
                assert response.status == 200
                activities = server._collector.get_activities()
                assert len(activities) == 1

    @pytest.mark.asyncio
    async def test_handle_request_does_not_collect_when_no_collector(self):
        server = ResponseServer()
        # Explicitly ensure no collector is set
        server._collector = None
        
        async with TestServer(server._app) as test_server:
            async with TestClient(test_server) as client:
                activity_data = {"type": "message", "text": "Hello"}
                response = await client.post(
                    "/v3/conversations/test/activities",
                    json=activity_data,
                )
                # Should still return 200 even without collector
                assert response.status == 200


class TestResponseServerIntegration:
    """Integration tests for ResponseServer."""

    @pytest.mark.asyncio
    async def test_full_workflow_send_and_collect_activities(self):
        server = ResponseServer(port=19891)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                # Send various activity types
                activities_to_send = [
                    {"type": "message", "text": "Hello"},
                    {"type": "message", "text": "World"},
                    {"type": ActivityTypes.typing},
                    {"type": "event", "name": "test_event"},
                ]
                for activity_data in activities_to_send:
                    async with session.post(
                        f"{server.service_endpoint}integration-test/activities",
                        json=activity_data,
                    ) as response:
                        pass

                collected = collector.get_activities()
                assert len(collected) == 4
                assert collected[0].text == "Hello"
                assert collected[1].text == "World"
                assert collected[2].type == ActivityTypes.typing
                assert collected[3].type == "event"

    @pytest.mark.asyncio
    async def test_collector_pop_returns_new_activities_only(self):
        server = ResponseServer(port=19892)
        async with server.listen() as collector:
            async with aiohttp.ClientSession() as session:
                # Send first batch
                async with session.post(
                    f"{server.service_endpoint}test/activities",
                    json={"type": "message", "text": "First"},
                ) as response:
                    pass
                first_pop = collector.pop()
                assert len(first_pop) == 1

                # Send second batch
                async with session.post(
                    f"{server.service_endpoint}test/activities",
                    json={"type": "message", "text": "Second"},
                ) as response:
                    pass
                second_pop = collector.pop()
                assert len(second_pop) == 1
                assert second_pop[0].text == "Second"