# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for ConversationsOperations using aiohttp TestServer."""

import json

import pytest
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import Activity, Channels, ResourceResponse, RoleTypes
from microsoft_agents.activity.channel_account import ChannelAccount
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


class TestNormalizeConversationId:
    """Tests for ConversationsOperations._normalize_conversation_id and _should_url_encode_conversation_id."""

    def _make_ops(self):
        return ConversationsOperations(None)

    # --- _should_url_encode_conversation_id ---

    @pytest.mark.parametrize(
        "channel, role",
        [
            (Channels.agents, RoleTypes.agentic_identity),
            (Channels.agents, RoleTypes.agentic_user),
            (Channels.ms_teams, RoleTypes.agentic_identity),
            (Channels.ms_teams, RoleTypes.agentic_user),
        ],
    )
    def test_should_url_encode_when_agentic_channel_and_agentic_role(self, channel, role):
        activity = Activity(
            type="message",
            channel_id=channel,
            from_property=ChannelAccount(id="user1", role=role),
        )
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is True

    @pytest.mark.parametrize(
        "channel",
        [Channels.agents, Channels.ms_teams],
    )
    @pytest.mark.parametrize(
        "role",
        [RoleTypes.user, RoleTypes.agent, RoleTypes.skill],
    )
    def test_should_not_url_encode_when_non_agentic_role(self, channel, role):
        activity = Activity(
            type="message",
            channel_id=channel,
            from_property=ChannelAccount(id="user1", role=role),
        )
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is False

    @pytest.mark.parametrize(
        "channel",
        [Channels.email, Channels.direct_line, Channels.webchat, Channels.emulator],
    )
    def test_should_not_url_encode_when_non_agentic_channel(self, channel):
        activity = Activity(
            type="message",
            channel_id=channel,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is False

    def test_should_not_url_encode_when_no_channel_id(self):
        activity = Activity(
            type="message",
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is False

    def test_should_not_url_encode_when_no_from(self):
        activity = Activity(type="message", channel_id=Channels.agents)
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is False

    def test_should_not_url_encode_when_no_role(self):
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1"),
        )
        assert ConversationsOperations._should_url_encode_conversation_id(activity) is False

    # --- _normalize_conversation_id ---

    def test_normalize_truncates_to_max_length(self):
        ops = self._make_ops()
        long_id = "a" * 200
        result = ops._normalize_conversation_id(long_id)
        assert result == "a" * 150

    def test_normalize_does_not_url_encode_without_activity(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        result = ops._normalize_conversation_id(conv_id)
        assert result == conv_id

    def test_normalize_url_encodes_for_agents_channel_with_agentic_role(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv%2Fwith%2Fslashes"

    def test_normalize_url_encodes_for_agents_subchannel(self):
        """Test that agents:email sub-channel also triggers URL encoding."""
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id="agents:email",
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv%2Fwith%2Fslashes"

    def test_normalize_url_encodes_for_msteams_with_agentic_role(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id=Channels.ms_teams,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv%2Fwith%2Fslashes"

    def test_normalize_truncates_before_url_encoding(self):
        ops = ConversationsOperations(None, max_conversation_id_length=5)
        conv_id = "ab/cd/ef"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        # Truncated to 5 chars first: "ab/cd", then URL encoded
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "ab%2Fcd"

    def test_normalize_no_url_encode_for_non_agentic_role_with_agents_channel(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == conv_id


class TestSendToConversationUrlEncoding:
    """Integration tests: URL encoding of conversation_id in send_to_conversation."""

    @pytest.mark.asyncio
    async def test_send_to_conversation_encodes_conversation_id_for_agentic_agents_channel(
        self,
    ):
        captured = {}

        async def handler(request):
            captured["raw_path"] = request.raw_path
            return web.json_response({"id": "resp-1"})

        routes = [web.post("/v3/conversations/{tail:.*}/activities", handler)]
        app = web.Application()
        app.router.add_routes(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                activity = Activity(
                    type="message",
                    channel_id=Channels.agents,
                    from_property=ChannelAccount(
                        id="user1", role=RoleTypes.agentic_identity
                    ),
                )
                await ops.send_to_conversation("conv/sub/id", activity)

            assert "conv%2Fsub%2Fid" in captured["raw_path"]
        finally:
            await server.close()


class TestReplyToActivityUrlEncoding:
    """Integration tests: URL encoding of conversation_id in reply_to_activity."""

    @pytest.mark.asyncio
    async def test_reply_to_activity_encodes_conversation_id_for_agentic_agents_channel(
        self,
    ):
        captured = {}

        async def handler(request):
            captured["raw_path"] = request.raw_path
            return web.json_response({"id": "resp-1"})

        routes = [
            web.post(
                "/v3/conversations/{tail:.*}/activities/{activity_id}", handler
            )
        ]
        app = web.Application()
        app.router.add_routes(routes)

        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                ops = ConversationsOperations(session)
                activity = Activity(
                    type="message",
                    channel_id=Channels.ms_teams,
                    from_property=ChannelAccount(
                        id="user1", role=RoleTypes.agentic_user
                    ),
                )
                await ops.reply_to_activity("conv/sub/id", "act-1", activity)

            assert "conv%2Fsub%2Fid" in captured["raw_path"]
        finally:
            await server.close()
