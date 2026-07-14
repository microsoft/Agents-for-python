# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for UserToken Bot Framework operations."""

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from microsoft_agents.hosting.core.connector.client.user_token_client import UserToken


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

    @pytest.mark.parametrize(
        ("channel_id", "expected"),
        [
            ("msteams", "msteams"),
            ("msteams:COPILOT", "msteams"),
            ("msteams:", "msteams"),
            (":COPILOT", ":COPILOT"),
            (" ", " "),
            (None, None),
        ],
    )
    def test_base_channel_id(self, channel_id, expected):
        assert UserToken._base_channel_id(channel_id) == expected
