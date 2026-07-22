# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.file_consent (fileConsent/invoke activities)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api.models import FileConsentCardResponse
    from microsoft_agents.hosting.msteams import TeamsAgentExtension

_PATCH = (
    "microsoft_agents.hosting.msteams.file_consent.file_consent._send_invoke_response"
)


class TestFileConsent:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_accept_selector(self):
        @self.ext.file_consent.accept()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="fileConsent/invoke",
                    value={"action": "accept"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="fileConsent/invoke",
                    value={"action": "decline"},
                )
            )
            is False
        )

    def test_decline_selector(self):
        @self.ext.file_consent.decline()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="fileConsent/invoke",
                    value={"action": "decline"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="fileConsent/invoke",
                    value={"action": "accept"},
                )
            )
            is False
        )

    def test_accept_is_invoke(self):
        @self.ext.file_consent.accept()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_decline_is_invoke(self):
        @self.ext.file_consent.decline()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_accept_handler_parses_response_and_sends_empty_invoke_response(self):
        user_handler = AsyncMock()

        @self.ext.file_consent.accept()
        async def handler(ctx, state, data: FileConsentCardResponse):
            await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "accept", "context": None, "uploadInfo": None},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], FileConsentCardResponse)
            mock_send.assert_awaited_once_with(ctx)

    @pytest.mark.asyncio
    async def test_decline_handler_parses_response_and_sends_empty_invoke_response(
        self,
    ):
        user_handler = AsyncMock()

        @self.ext.file_consent.decline()
        async def handler(ctx, state, data: FileConsentCardResponse):
            await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "decline", "context": None, "uploadInfo": None},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], FileConsentCardResponse)
            mock_send.assert_awaited_once_with(ctx)

    def test_accept_direct_decorator_style(self):
        @self.ext.file_consent.accept  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_decline_direct_decorator_style(self):
        @self.ext.file_consent.decline  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None
