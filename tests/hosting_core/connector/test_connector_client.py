# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for ConversationsOperations using aiohttp TestServer."""

import pytest
from aiohttp import ClientResponseError, web, ClientSession
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    AttachmentData,
    ChannelAccount,
    Channels,
    ConversationParameters,
    ResourceResponse,
    RoleTypes,
    Transcript,
)
from microsoft_agents.hosting.core.connector.client.connector_client import (
    ConnectorClient,
    ConversationsOperations,
)
from microsoft_agents.hosting.core.header_propagation import HeaderPropagationContext


def _create_app(routes):
    """Create an aiohttp app with the given route table."""
    app = web.Application()
    app.router.add_routes(routes)
    return app


class _HeaderProvider:
    def __init__(self, headers: dict[str, str]):
        self.headers = headers

    def get_headers(self) -> dict[str, str]:
        return dict(self.headers)


@pytest.fixture(autouse=True)
def reset_header_propagation_context():
    HeaderPropagationContext.reset()
    yield
    HeaderPropagationContext.reset()


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


class TestConnectorClientHeaderPropagation:
    """Tests propagated headers through a full ConnectorClient operation."""

    @pytest.mark.asyncio
    async def test_send_to_conversation_uses_headers_registered_after_client_creation(
        self,
    ):
        captured = {}

        async def handler(request):
            captured["headers"] = request.headers
            return web.json_response({"id": "activity-id-123"})

        app = _create_app(
            [web.post("/v3/conversations/{conversation_id}/activities", handler)]
        )
        server = TestServer(app)
        await server.start_server()

        client = ConnectorClient(str(server.make_url("/")), token="")
        try:
            HeaderPropagationContext.register(
                _HeaderProvider({"X-Agentic-Test": "propagated"})
            )

            result = await client.conversations.send_to_conversation(
                "conv-1", Activity(type="message", text="hello")
            )

            assert result.id == "activity-id-123"
            assert captured["headers"]["X-Agentic-Test"] == "propagated"
        finally:
            await client.close()
            await server.close()


class TestConnectorClientContract:
    """Tests the externally observable Connector REST contract."""

    @pytest.mark.asyncio
    async def test_conversation_lifecycle_uses_expected_requests_and_models(self):
        requests = []

        async def handler(request):
            body = await request.json() if request.can_read_body else None
            requests.append(
                {
                    "method": request.method,
                    "path": request.path,
                    "query": dict(request.query),
                    "body": body,
                }
            )
            if request.method == "GET":
                return web.json_response(
                    {"continuationToken": "next-page", "conversations": []}
                )
            if request.path == "/v3/conversations":
                return web.json_response({"id": "new-conversation"}, status=201)
            if request.method == "DELETE":
                return web.Response(status=202)
            return web.json_response({"id": "activity-result"}, status=202)

        app = _create_app([web.route("*", "/{tail:.*}", handler)])
        server = TestServer(app)
        await server.start_server()
        client = ConnectorClient(str(server.make_url("/")), token="")
        try:
            conversations = await client.conversations.get_conversations("page-1")
            created = await client.conversations.create_conversation(
                ConversationParameters(
                    is_group=True,
                    bot=ChannelAccount(id="agent-1"),
                    members=[ChannelAccount(id="member-1")],
                    topic_name="Planning",
                )
            )
            updated = await client.conversations.update_activity(
                "conversation-1",
                "activity-1",
                Activity(type="message", text="updated"),
            )
            await client.conversations.delete_activity("conversation-1", "activity-1")
            history = await client.conversations.send_conversation_history(
                "conversation-1",
                Transcript(
                    activities=[Activity(type="message", text="Earlier message")]
                ),
            )
        finally:
            await client.close()
            await server.close()

        assert conversations.continuation_token == "next-page"
        assert created.id == "new-conversation"
        assert updated.id == "activity-result"
        assert history.id == "activity-result"
        assert requests == [
            {
                "method": "GET",
                "path": "/v3/conversations",
                "query": {"continuationToken": "page-1"},
                "body": None,
            },
            {
                "method": "POST",
                "path": "/v3/conversations",
                "query": {},
                "body": {
                    "isGroup": True,
                    "bot": {"id": "agent-1"},
                    "members": [{"id": "member-1"}],
                    "topicName": "Planning",
                },
            },
            {
                "method": "PUT",
                "path": "/v3/conversations/conversation-1/activities/activity-1",
                "query": {},
                "body": {"type": "message", "text": "updated"},
            },
            {
                "method": "DELETE",
                "path": "/v3/conversations/conversation-1/activities/activity-1",
                "query": {},
                "body": None,
            },
            {
                "method": "POST",
                "path": "/v3/conversations/conversation-1/activities/history",
                "query": {},
                "body": {
                    "activities": [{"type": "message", "text": "Earlier message"}]
                },
            },
        ]

    @pytest.mark.asyncio
    async def test_members_paging_and_upload_use_expected_requests(self):
        requests = []

        async def handler(request):
            body = await request.json() if request.can_read_body else None
            requests.append((request.method, request.path, dict(request.query), body))
            if request.path.endswith("/pagedmembers"):
                return web.json_response(
                    {
                        "continuationToken": "next",
                        "members": [{"id": "member-2", "name": "Ada"}],
                    }
                )
            if request.path.endswith("/members/member-1"):
                if request.method == "DELETE":
                    return web.Response(status=204)
                return web.json_response({"id": "member-1", "name": "Lin"})
            if request.path.endswith("/members"):
                return web.json_response([{"id": "member-1", "name": "Lin"}])
            if request.path.endswith("/attachments"):
                return web.json_response({"id": "attachment-1"})
            raise AssertionError(f"Unexpected request: {request.method} {request.path}")

        app = _create_app([web.route("*", "/{tail:.*}", handler)])
        server = TestServer(app)
        await server.start_server()
        client = ConnectorClient(str(server.make_url("/")), token="")
        try:
            members = await client.conversations.get_conversation_members(
                "conversation-1"
            )
            member = await client.conversations.get_conversation_member(
                "conversation-1", "member-1"
            )
            page = await client.conversations.get_conversation_paged_members(
                "conversation-1", page_size=25, continuation_token="page-1"
            )
            await client.conversations.delete_conversation_member(
                "conversation-1", "member-1"
            )
            attachment = AttachmentData(
                name="notes.txt",
                type="text/plain",
                original_base64=b"dGVzdA==",
            )
            uploaded = await client.conversations.upload_attachment(
                "conversation-1",
                attachment,
            )
        finally:
            await client.close()
            await server.close()

        assert members[0].id == "member-1"
        assert member.name == "Lin"
        assert page.members[0].id == "member-2"
        assert uploaded.id == "attachment-1"
        assert requests == [
            (
                "GET",
                "/v3/conversations/conversation-1/members",
                {},
                None,
            ),
            (
                "GET",
                "/v3/conversations/conversation-1/members/member-1",
                {},
                None,
            ),
            (
                "GET",
                "/v3/conversations/conversation-1/pagedmembers",
                {"pageSize": "25", "continuationToken": "page-1"},
                None,
            ),
            (
                "DELETE",
                "/v3/conversations/conversation-1/members/member-1",
                {},
                None,
            ),
            (
                "POST",
                "/v3/conversations/conversation-1/attachments",
                {},
                {
                    "name": "notes.txt",
                    "originalBase64": "dGVzdA==",
                    "type": "text/plain",
                },
            ),
        ]

    @pytest.mark.asyncio
    async def test_attachment_operations_return_metadata_and_binary_content(self):
        async def info_handler(request):
            return web.json_response(
                {
                    "name": "report.pdf",
                    "type": "application/pdf",
                    "views": [{"viewId": "original"}],
                }
            )

        async def content_handler(request):
            return web.Response(body=b"attachment bytes")

        app = _create_app(
            [
                web.get("/v3/attachments/{attachment_id}", info_handler),
                web.get(
                    "/v3/attachments/{attachment_id}/views/{view_id}",
                    content_handler,
                ),
            ]
        )
        server = TestServer(app)
        await server.start_server()
        client = ConnectorClient(str(server.make_url("/")), token="")
        try:
            info = await client.attachments.get_attachment_info("attachment-1")
            content = await client.attachments.get_attachment(
                "attachment-1", "original"
            )
        finally:
            await client.close()
            await server.close()

        assert info.name == "report.pdf"
        assert info.type == "application/pdf"
        assert info.views == [{"viewId": "original"}]
        assert content.read() == b"attachment bytes"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [302, 400, 500])
    async def test_unexpected_response_status_raises_client_response_error(
        self, status
    ):
        async def handler(request):
            return web.Response(status=status)

        app = _create_app(
            [web.post("/v3/conversations/{conversation_id}/activities", handler)]
        )
        server = TestServer(app)
        await server.start_server()
        client = ConnectorClient(str(server.make_url("/")), token="")
        try:
            with pytest.raises(ClientResponseError) as exc_info:
                await client.conversations.send_to_conversation(
                    "conversation-1", Activity(type="message", text="hello")
                )
        finally:
            await client.close()
            await server.close()

        assert exc_info.value.status == status
        if status == 302:
            assert (
                exc_info.value.message == "Error accessing resource "
                "'v3/conversations/conversation-1/activities'"
            )


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
    """Tests for ConversationsOperations._normalize_conversation_id and _should_sanitize_conversation_id."""

    def _make_ops(self):
        return ConversationsOperations(None)

    # --- _should_sanitize_conversation_id ---

    @pytest.mark.parametrize(
        "role",
        [RoleTypes.agentic_identity, RoleTypes.agentic_user],
    )
    def test_should_sanitize_when_agents_channel_and_agentic_role(self, role):
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=role),
        )
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is True
        )

    @pytest.mark.parametrize(
        "role",
        [RoleTypes.user, RoleTypes.agent, RoleTypes.skill],
    )
    def test_should_not_sanitize_when_non_agentic_role(self, role):
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=role),
        )
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is False
        )

    @pytest.mark.parametrize(
        "channel",
        [
            Channels.ms_teams,
            Channels.email,
            Channels.direct_line,
            Channels.webchat,
            Channels.emulator,
        ],
    )
    def test_should_not_sanitize_when_non_agents_channel(self, channel):
        activity = Activity(
            type="message",
            channel_id=channel,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is False
        )

    def test_should_not_sanitize_when_no_channel_id(self):
        activity = Activity(
            type="message",
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is False
        )

    def test_should_not_sanitize_when_no_from(self):
        activity = Activity(type="message", channel_id=Channels.agents)
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is False
        )

    def test_should_not_sanitize_when_no_role(self):
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1"),
        )
        assert (
            ConversationsOperations._should_sanitize_conversation_id(activity) is False
        )

    # --- _normalize_conversation_id ---

    def test_normalize_truncates_to_max_length(self):
        ops = self._make_ops()
        long_id = "a" * 200
        result = ops._normalize_conversation_id(long_id)
        assert result == "a" * 150

    def test_normalize_does_not_sanitize_without_activity(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        result = ops._normalize_conversation_id(conv_id)
        assert result == conv_id

    def test_normalize_sanitizes_slashes_for_agents_channel_with_agentic_role(self):
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv_with_slashes"

    def test_normalize_sanitizes_all_path_chars_for_agents_channel(self):
        """Test that /, \\, #, and ? are all replaced with _."""
        ops = self._make_ops()
        conv_id = "conv/with\\special#chars?here"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv_with_special_chars_here"

    def test_normalize_sanitizes_for_agents_subchannel(self):
        """Test that agents:email sub-channel also triggers sanitization."""
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id="agents:email",
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "conv_with_slashes"

    def test_normalize_does_not_sanitize_for_msteams_with_agentic_role(self):
        """msteams channel should NOT sanitize the conversation ID."""
        ops = self._make_ops()
        conv_id = "conv/with/slashes"
        activity = Activity(
            type="message",
            channel_id=Channels.ms_teams,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_user),
        )
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == conv_id

    def test_normalize_truncates_before_sanitizing(self):
        ops = ConversationsOperations(None, max_conversation_id_length=5)
        conv_id = "ab/cd/ef"
        activity = Activity(
            type="message",
            channel_id=Channels.agents,
            from_property=ChannelAccount(id="user1", role=RoleTypes.agentic_identity),
        )
        # Truncated to 5 chars first: "ab/cd", then sanitized
        result = ops._normalize_conversation_id(conv_id, activity)
        assert result == "ab_cd"

    def test_normalize_no_sanitize_for_non_agentic_role_with_agents_channel(self):
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
    """Integration tests: sanitization of conversation_id in send_to_conversation."""

    @pytest.mark.asyncio
    async def test_send_to_conversation_sanitizes_conversation_id_for_agentic_agents_channel(
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

            assert "conv_sub_id" in captured["raw_path"]
        finally:
            await server.close()


class TestReplyToActivityUrlEncoding:
    """Integration tests: sanitization of conversation_id in reply_to_activity."""

    @pytest.mark.asyncio
    async def test_reply_to_activity_sanitizes_conversation_id_for_agentic_agents_channel(
        self,
    ):
        captured = {}

        async def handler(request):
            captured["raw_path"] = request.raw_path
            return web.json_response({"id": "resp-1"})

        routes = [
            web.post("/v3/conversations/{tail:.*}/activities/{activity_id}", handler)
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
                    channel_id=Channels.agents,
                    from_property=ChannelAccount(
                        id="user1", role=RoleTypes.agentic_user
                    ),
                )
                await ops.reply_to_activity("conv/sub/id", "act-1", activity)

            assert "conv_sub_id" in captured["raw_path"]
        finally:
            await server.close()
