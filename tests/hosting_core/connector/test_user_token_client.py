# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for UserToken Bot Framework operations."""

import base64
import json

import pytest
from aiohttp import ClientResponseError, ClientSession, web
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    ChannelId,
    ConversationAccount,
    TokenExchangeRequest,
)
from microsoft_agents.hosting.core.connector.client.user_token_client import (
    UserToken,
    UserTokenClient,
)
from microsoft_agents.hosting.core.header_propagation import HeaderPropagationContext


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


class TestUserTokenBaseChannel:
    """Bot Framework token operations use the base channel partition."""

    @pytest.mark.asyncio
    async def test_all_token_operations_normalize_composite_channel(self):
        captured = []

        async def handler(request):
            captured.append(
                (request.method, request.path, request.query.get("channelId"))
            )
            path = request.path.lower()
            if path.endswith("/gettokenorsigninresource"):
                return web.json_response({"tokenResponse": {"token": "token"}})
            if path.endswith("/gettoken") or path.endswith("/exchange"):
                return web.json_response({"token": "token"})
            if path.endswith("/getaadtokens"):
                return web.json_response({"resource": {"token": "token"}})
            if path.endswith("/gettokenstatus"):
                return web.json_response([])
            if path.endswith("/signout"):
                return web.Response(status=204)
            raise AssertionError(f"Unexpected token operation: {request.path}")

        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", handler)
        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                user_token = UserToken(session)
                args = {
                    "user_id": "user",
                    "connection_name": "connection",
                    "channel_id": "msteams:COPILOT",
                }
                await user_token.get_token(**args)
                await user_token._get_token_or_sign_in_resource(**args, state="state")
                await user_token.get_aad_tokens(**args)
                await user_token.sign_out(**args)
                await user_token.get_token_status(
                    user_id="user", channel_id="msteams:COPILOT"
                )
                await user_token.exchange_token(**args)
        finally:
            await server.close()

        assert len(captured) == 6
        assert all(channel_id == "msteams" for _, _, channel_id in captured)

    @pytest.mark.asyncio
    async def test_optional_channel_is_omitted_when_none(self):
        captured = []

        async def handler(request):
            captured.append(request.query.get("channelId"))
            path = request.path.lower()
            if path.endswith("/gettoken"):
                return web.json_response({"token": "token"})
            if path.endswith("/getaadtokens"):
                return web.json_response({"resource": {"token": "token"}})
            if path.endswith("/gettokenstatus"):
                return web.json_response([])
            if path.endswith("/signout"):
                return web.Response(status=204)
            raise AssertionError(f"Unexpected token operation: {request.path}")

        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", handler)
        server = TestServer(app)
        await server.start_server()
        try:
            async with ClientSession(base_url=server.make_url("/")) as session:
                user_token = UserToken(session)
                await user_token.get_token("user", "connection")
                await user_token.get_aad_tokens("user", "connection")
                await user_token.sign_out("user", "connection")
                await user_token.get_token_status("user")
        finally:
            await server.close()

        assert captured == [None, None, None, None]


class TestUserTokenClientHeaderPropagation:
    """Tests propagated headers through UserTokenClient operations."""

    @pytest.mark.asyncio
    async def test_get_user_token_uses_headers_registered_after_client_creation(self):
        captured = {}

        async def handler(request):
            captured["headers"] = request.headers
            return web.json_response({"token": "token"})

        app = web.Application()
        app.router.add_get("/api/usertoken/GetToken", handler)
        server = TestServer(app)
        await server.start_server()

        client = UserTokenClient(str(server.make_url("/")), token="", app_id="app-id")
        try:
            HeaderPropagationContext.register(
                _HeaderProvider({"X-Agentic-Test": "propagated"})
            )

            result = await client.get_user_token("user", "connection", "msteams")

            assert result.token == "token"
            assert captured["headers"]["X-Agentic-Test"] == "propagated"
        finally:
            await client.close()
            await server.close()


class TestUserTokenClientContract:
    """Tests the externally observable OAuth token service contract."""

    @pytest.mark.asyncio
    async def test_token_operations_use_expected_requests_and_typed_responses(self):
        requests = []

        async def handler(request):
            body = await request.json() if request.can_read_body else None
            requests.append((request.method, request.path, dict(request.query), body))
            if request.path.endswith("/GetToken"):
                return web.json_response(
                    {"token": "user-token", "connectionName": "connection"}
                )
            if request.path.endswith("/SignOut"):
                return web.Response(status=204)
            if request.path.endswith("/GetTokenStatus"):
                return web.json_response(
                    [{"connectionName": "connection", "hasToken": True}]
                )
            if request.path.endswith("/GetAadTokens"):
                return web.json_response(
                    {"https://graph.microsoft.com": {"token": "graph-token"}}
                )
            if request.path.endswith("/exchange"):
                return web.json_response({"token": "exchanged-token"})
            raise AssertionError(f"Unexpected token operation: {request.path}")

        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", handler)
        server = TestServer(app)
        await server.start_server()
        client = UserTokenClient(str(server.make_url("/")), token="", app_id="app-id")
        try:
            token = await client.get_user_token(
                "user-1", "connection", "msteams:copilot", "magic-code"
            )
            await client.sign_out_user("user-1", "connection", "msteams:copilot")
            statuses = await client.get_token_status(
                "user-1", "msteams:copilot", include="configured"
            )
            aad_tokens = await client.get_aad_tokens(
                "user-1",
                "connection",
                ["https://graph.microsoft.com"],
                "msteams:copilot",
            )
            exchanged = await client.exchange_token(
                "user-1",
                "connection",
                "msteams:copilot",
                TokenExchangeRequest(uri="api://resource", token="subject-token"),
            )
        finally:
            await client.close()
            await server.close()

        assert token.token == "user-token"
        assert statuses[0].connection_name == "connection"
        assert statuses[0].has_token is True
        assert aad_tokens["https://graph.microsoft.com"].token == "graph-token"
        assert exchanged.token == "exchanged-token"
        assert requests == [
            (
                "GET",
                "/api/usertoken/GetToken",
                {
                    "userId": "user-1",
                    "connectionName": "connection",
                    "channelId": "msteams",
                    "code": "magic-code",
                },
                None,
            ),
            (
                "DELETE",
                "/api/usertoken/SignOut",
                {
                    "userId": "user-1",
                    "connectionName": "connection",
                    "channelId": "msteams",
                },
                None,
            ),
            (
                "GET",
                "/api/usertoken/GetTokenStatus",
                {
                    "userId": "user-1",
                    "channelId": "msteams",
                    "include": "configured",
                },
                None,
            ),
            (
                "POST",
                "/api/usertoken/GetAadTokens",
                {
                    "userId": "user-1",
                    "connectionName": "connection",
                    "channelId": "msteams",
                },
                {"resourceUrls": ["https://graph.microsoft.com"]},
            ),
            (
                "POST",
                "/api/usertoken/exchange",
                {
                    "userId": "user-1",
                    "connectionName": "connection",
                    "channelId": "msteams",
                },
                {"uri": "api://resource", "token": "subject-token"},
            ),
        ]

    @pytest.mark.asyncio
    async def test_sign_in_requests_carry_activity_context_in_encoded_state(self):
        requests = []

        async def handler(request):
            requests.append((request.path, dict(request.query)))
            if request.path.endswith("/getSignInResource"):
                return web.json_response({"signInLink": "https://sign-in.example"})
            return web.json_response({"tokenResponse": {"token": "existing-token"}})

        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", handler)
        server = TestServer(app)
        await server.start_server()
        client = UserTokenClient(str(server.make_url("/")), token="", app_id="app-id")
        activity = Activity(
            type="message",
            id="activity-1",
            channel_id=ChannelId("msteams:copilot"),
            service_url="https://service.example",
            from_property=ChannelAccount(id="user-1"),
            recipient=ChannelAccount(id="agent-1"),
            conversation=ConversationAccount(id="conversation-1"),
        )
        try:
            sign_in = await client.get_sign_in_resource(
                "connection", activity, final_redirect="https://app.example/done"
            )
            token_or_sign_in = await client.get_token_or_sign_in_resource(
                "connection",
                activity,
                code="magic-code",
                final_redirect="https://app.example/done",
                fwd_url="https://app.example/forward",
            )
        finally:
            await client.close()
            await server.close()

        assert sign_in.sign_in_link == "https://sign-in.example"
        assert token_or_sign_in.token_response.token == "existing-token"

        sign_in_path, sign_in_query = requests[0]
        token_path, token_query = requests[1]
        sign_in_state = json.loads(
            base64.b64decode(sign_in_query.pop("state")).decode()
        )
        token_state = json.loads(base64.b64decode(token_query.pop("state")).decode())
        expected_state = {
            "connectionName": "connection",
            "conversation": {
                "activityId": "activity-1",
                "user": {"id": "user-1"},
                "bot": {"id": "agent-1"},
                "conversation": {"id": "conversation-1"},
                "channelId": "msteams",
                "serviceUrl": "https://service.example",
            },
            "msAppId": "app-id",
        }
        assert sign_in_path == "/api/botsignin/getSignInResource"
        assert sign_in_query == {"finalRedirect": "https://app.example/done"}
        assert sign_in_state == expected_state
        assert token_path == "/api/usertoken/GetTokenOrSignInResource"
        assert token_query == {
            "userId": "user-1",
            "connectionName": "connection",
            "channelId": "msteams",
            "code": "magic-code",
            "finalRedirect": "https://app.example/done",
            "fwdUrl": "https://app.example/forward",
        }
        assert token_state == expected_state

    @pytest.mark.asyncio
    async def test_missing_context_is_rejected_before_a_sign_in_request(self):
        client_without_app_id = UserTokenClient(
            "https://token.example", token="", app_id=None
        )
        activity = Activity(
            type="message",
            from_property=ChannelAccount(id="user-1"),
        )
        try:
            with pytest.raises(ValueError, match="App ID must be provided"):
                await client_without_app_id.get_sign_in_resource("connection", activity)

            client_with_app_id = UserTokenClient(
                "https://token.example", token="", app_id="app-id"
            )
            try:
                with pytest.raises(ValueError, match="Activity must have a channel_id"):
                    await client_with_app_id.get_token_or_sign_in_resource(
                        "connection", activity
                    )
            finally:
                await client_with_app_id.close()
        finally:
            await client_without_app_id.close()

    @pytest.mark.asyncio
    async def test_missing_user_token_returns_an_empty_token_response(self):
        async def handler(request):
            return web.Response(status=404)

        app = web.Application()
        app.router.add_get("/api/usertoken/GetToken", handler)
        server = TestServer(app)
        await server.start_server()
        client = UserTokenClient(str(server.make_url("/")), token="", app_id="app-id")
        try:
            token = await client.get_user_token("user-1", "connection", "msteams")
        finally:
            await client.close()
            await server.close()

        assert token.token is None
        assert not token

    @pytest.mark.asyncio
    async def test_token_service_failure_raises_client_response_error(self):
        async def handler(request):
            return web.Response(status=500)

        app = web.Application()
        app.router.add_get("/api/usertoken/GetTokenStatus", handler)
        server = TestServer(app)
        await server.start_server()
        client = UserTokenClient(str(server.make_url("/")), token="", app_id="app-id")
        try:
            with pytest.raises(ClientResponseError) as exc_info:
                await client.get_token_status("user-1", "msteams")
        finally:
            await client.close()
            await server.close()

        assert exc_info.value.status == 500
