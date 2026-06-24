# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.config (config/fetch and config/submit invokes)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_agents.hosting.msteams import TeamsAgentExtension

_PATCH = "microsoft_agents.hosting.msteams.config.config._send_invoke_response"


class TestConfig:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_fetch_selector(self):
        @self.ext.config.fetch()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.invoke, name="config/fetch")) is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="config/submit")) is False
        )

    def test_fetch_is_invoke(self):
        @self.ext.config.fetch()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_submit_selector(self):
        @self.ext.config.submit()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.invoke, name="config/submit")) is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="config/fetch")) is False
        )

    def test_submit_is_invoke(self):
        @self.ext.config.submit()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_fetch_handler_sends_response_when_returned(self):
        response = {"type": "auth", "suggestedActions": {}}
        user_handler = AsyncMock(return_value=response)

        @self.ext.config.fetch()
        async def handler(ctx, state, data):
            return await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="config/fetch", value={"setting": "value"}
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert user_handler.called
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_fetch_handler_skips_send_when_none_returned(self):
        @self.ext.config.fetch()
        async def handler(ctx, state, data): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(ActivityTypes.invoke, name="config/fetch", value={})
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fetch_handler_receives_raw_activity_value(self):
        user_handler = AsyncMock(return_value=None)

        @self.ext.config.fetch()
        async def handler(ctx, state, data):
            return await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        payload = {"key": "val"}
        ctx = _make_context(ActivityTypes.invoke, name="config/fetch", value=payload)
        with patch(_PATCH, new_callable=AsyncMock):
            await route_handler(ctx, MagicMock())
            assert user_handler.call_args[0][2] == payload
