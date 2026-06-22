# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.messages (message update and actionable message events)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_teams.api.models import O365ConnectorCardActionQuery
    from microsoft_agents.hosting.teams import TeamsAgentExtension

_PATCH = "microsoft_agents.hosting.teams.message.message._send_invoke_response"


class TestMessageEdit:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_edit_selector(self):
        @self.ext.messages.edit()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_data={"eventType": "editMessage"},
                )
            )
            is True
        )

    def test_edit_wrong_event_type(self):
        @self.ext.messages.edit()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_data={"eventType": "undeleteMessage"},
                )
            )
            is False
        )

    def test_edit_wrong_channel(self):
        @self.ext.messages.edit()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_id="webchat",
                    channel_data={"eventType": "editMessage"},
                )
            )
            is False
        )

    def test_edit_is_not_invoke(self):
        @self.ext.messages.edit()
        async def handler(ctx, state): ...

        assert self.app._routes[0]["is_invoke"] is False


class TestMessageUndelete:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_undelete_selector(self):
        @self.ext.messages.undelete()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_data={"eventType": "undeleteMessage"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_data={"eventType": "editMessage"},
                )
            )
            is False
        )


class TestMessageSoftDelete:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_soft_delete_selector(self):
        @self.ext.messages.delete()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_delete,
                    channel_data={"eventType": "softDeleteMessage"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_update,
                    channel_data={"eventType": "softDeleteMessage"},
                )
            )
            is False
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_delete,
                    channel_data={"eventType": "editMessage"},
                )
            )
            is False
        )

    def test_soft_delete_wrong_channel(self):
        @self.ext.messages.delete()
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.message_delete,
                    channel_id="webchat",
                    channel_data={"eventType": "softDeleteMessage"},
                )
            )
            is False
        )


class TestMessageReadReceipt:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_read_receipt_selector(self):
        @self.ext.messages.read_receipt()
        async def handler(ctx, state, receipt): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.readReceipt"
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.meetingStart"
                )
            )
            is False
        )

    def test_read_receipt_is_not_invoke(self):
        @self.ext.messages.read_receipt()
        async def handler(ctx, state, receipt): ...

        assert self.app._routes[0]["is_invoke"] is False

    @pytest.mark.asyncio
    async def test_read_receipt_handler_receives_dict(self):
        user_handler = AsyncMock()

        @self.ext.messages.read_receipt()
        async def handler(ctx, state, receipt):
            await user_handler(ctx, state, receipt)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.readReceipt",
            value={"lastReadMessageId": "msg123"},
        )
        await route_handler(ctx, MagicMock())
        assert user_handler.call_args[0][2] == {"lastReadMessageId": "msg123"}

    @pytest.mark.asyncio
    async def test_read_receipt_raises_on_non_dict_value(self):
        @self.ext.messages.read_receipt()
        async def handler(ctx, state, receipt): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.readReceipt",
            value='{"lastReadMessageId": "msg123"}',
        )
        with pytest.raises(TypeError, match="read_receipt"):
            await route_handler(ctx, MagicMock())


class TestMessageExecuteAction:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_execute_action_selector(self):
        @self.ext.messages.execute_action()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke, name="actionableMessage/executeAction"
                )
            )
            is True
        )
        assert selector(_make_context(ActivityTypes.invoke, name="task/fetch")) is False

    def test_execute_action_is_invoke(self):
        @self.ext.messages.execute_action()
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_execute_action_parses_query_and_sends_empty_response(self):
        user_handler = AsyncMock()

        @self.ext.messages.execute_action()
        async def handler(ctx, state, query: O365ConnectorCardActionQuery):
            await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="actionableMessage/executeAction", value={}
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(
                user_handler.call_args[0][2], O365ConnectorCardActionQuery
            )
            mock_send.assert_awaited_once_with(ctx)


class TestMessageDirectDecoratorStyle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_edit_direct(self):
        @self.ext.messages.edit  # type: ignore[arg-type]
        async def handler(ctx, state): ...

        assert self.app._routes[0]["selector"] is not None

    def test_undelete_direct(self):
        @self.ext.messages.undelete  # type: ignore[arg-type]
        async def handler(ctx, state): ...

        assert self.app._routes[0]["selector"] is not None

    def test_soft_delete_direct(self):
        @self.ext.messages.delete  # type: ignore[arg-type]
        async def handler(ctx, state): ...

        assert self.app._routes[0]["selector"] is not None

    def test_read_receipt_direct(self):
        @self.ext.messages.read_receipt  # type: ignore[arg-type]
        async def handler(ctx, state, value): ...

        assert self.app._routes[0]["selector"] is not None

    def test_execute_action_direct(self):
        @self.ext.messages.execute_action  # type: ignore[arg-type]
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["selector"] is not None
