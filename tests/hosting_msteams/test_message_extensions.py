# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.message_extensions (composeExtension invokes)."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api.models import (
        AppBasedLinkQuery,
        MessagingExtensionAction,
        MessagingExtensionQuery,
        MessagingExtensionResponse,
    )
    from microsoft_agents.hosting.msteams import TeamsAgentExtension

_PATCH = "microsoft_agents.hosting.msteams.message_extension.message_extension._send_invoke_response"


class TestMessageExtensionQuery:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_query_matches_by_command_id(self):
        @self.ext.message_extensions.query("searchCmd")
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/query",
                    value={"commandId": "searchCmd"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/query",
                    value={"commandId": "other"},
                )
            )
            is False
        )

    def test_query_no_command_id_matches_all(self):
        @self.ext.message_extensions.query()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/query",
                    value={"commandId": "anything"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke, name="composeExtension/query", value={}
                )
            )
            is True
        )

    def test_query_wrong_invoke_name(self):
        @self.ext.message_extensions.query()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke, name="composeExtension/submitAction", value={}
                )
            )
            is False
        )

    def test_query_is_invoke(self):
        @self.ext.message_extensions.query()
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_query_handler_parses_query_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.query()
        async def handler(ctx, state, query: MessagingExtensionQuery):
            return await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/query",
            value={"commandId": "search"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], MessagingExtensionQuery)
            mock_send.assert_awaited_once_with(ctx, response)


class TestMessageExtensionSubmitAction:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_submit_action_excludes_preview(self):
        @self.ext.message_extensions.submit_action()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
                )
            )
            is False
        )

    def test_message_preview_edit_selector(self):
        @self.ext.message_extensions.message_preview_edit()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd", "botMessagePreviewAction": "send"},
                )
            )
            is False
        )

    def test_message_preview_send_selector(self):
        @self.ext.message_extensions.message_preview_send()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd", "botMessagePreviewAction": "send"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
                )
            )
            is False
        )

    def test_submit_action_is_invoke(self):
        @self.ext.message_extensions.submit_action()
        async def handler(ctx, state, action): ...

        assert self.app._routes[0]["is_invoke"] is True


class TestMessagePreviewEdit:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    @pytest.mark.asyncio
    async def test_handler_receives_deserialized_activity(self):
        from microsoft_agents.activity import Activity

        user_handler = AsyncMock()

        @self.ext.message_extensions.message_preview_edit()
        async def handler(ctx, state, preview):
            await user_handler(ctx, state, preview)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={
                "commandId": "cmd",
                "botMessagePreviewAction": "edit",
                "botActivityPreview": [{"type": "message", "text": "preview text"}],
            },
        )
        with patch(_PATCH, new_callable=AsyncMock):
            await route_handler(ctx, MagicMock())
        preview_arg = user_handler.call_args[0][2]
        assert isinstance(preview_arg, Activity)
        assert preview_arg.text == "preview text"

    @pytest.mark.asyncio
    async def test_raises_when_value_is_not_dict(self):
        @self.ext.message_extensions.message_preview_edit()
        async def handler(ctx, state, preview): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value=None,
        )
        with pytest.raises(ValueError, match="botActivityPreview"):
            await route_handler(ctx, MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_bot_activity_preview_is_empty(self):
        @self.ext.message_extensions.message_preview_edit()
        async def handler(ctx, state, preview): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={
                "commandId": "cmd",
                "botMessagePreviewAction": "edit",
                "botActivityPreview": [],
            },
        )
        with pytest.raises(ValueError, match="botActivityPreview"):
            await route_handler(ctx, MagicMock())


class TestMessagePreviewSend:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    @pytest.mark.asyncio
    async def test_handler_receives_deserialized_activity(self):
        from microsoft_agents.activity import Activity

        user_handler = AsyncMock(return_value=None)

        @self.ext.message_extensions.message_preview_send()
        async def handler(ctx, state, preview):
            return await user_handler(ctx, state, preview)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={
                "commandId": "cmd",
                "botMessagePreviewAction": "send",
                "botActivityPreview": [{"type": "message", "text": "send text"}],
            },
        )
        with patch(_PATCH, new_callable=AsyncMock):
            await route_handler(ctx, MagicMock())
        preview_arg = user_handler.call_args[0][2]
        assert isinstance(preview_arg, Activity)
        assert preview_arg.text == "send text"

    @pytest.mark.asyncio
    async def test_raises_when_value_is_not_dict(self):
        @self.ext.message_extensions.message_preview_send()
        async def handler(ctx, state, preview): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value=None,
        )
        with pytest.raises(ValueError, match="botActivityPreview"):
            await route_handler(ctx, MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_bot_activity_preview_missing(self):
        @self.ext.message_extensions.message_preview_send()
        async def handler(ctx, state, preview): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "send"},
        )
        with pytest.raises(ValueError, match="botActivityPreview"):
            await route_handler(ctx, MagicMock())


class TestMessageExtensionFetchAction:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_fetch_action_matches_command_id(self):
        @self.ext.message_extensions.fetch_action("myCmd")
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/fetchTask",
                    value={"commandId": "myCmd"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/fetchTask",
                    value={"commandId": "other"},
                )
            )
            is False
        )

    def test_fetch_action_no_command_id_matches_all(self):
        @self.ext.message_extensions.fetch_action()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/fetchTask",
                    value={"commandId": "anything"},
                )
            )
            is True
        )

    def test_fetch_action_is_invoke(self):
        @self.ext.message_extensions.fetch_action()
        async def handler(ctx, state, action): ...

        assert self.app._routes[0]["is_invoke"] is True


class TestMessageExtensionLinkAndItem:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_query_link_selector(self):
        @self.ext.message_extensions.query_link()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(ActivityTypes.invoke, name="composeExtension/queryLink")
            )
            is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="composeExtension/query"))
            is False
        )

    def test_anonymous_query_link_selector(self):
        @self.ext.message_extensions.anonymous_query_link()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke, name="composeExtension/anonymousQueryLink"
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(ActivityTypes.invoke, name="composeExtension/queryLink")
            )
            is False
        )

    def test_select_item_selector(self):
        @self.ext.message_extensions.select_item()
        async def handler(ctx, state, item): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(ActivityTypes.invoke, name="composeExtension/selectItem")
            )
            is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="composeExtension/query"))
            is False
        )

    def test_query_link_is_invoke(self):
        @self.ext.message_extensions.query_link()
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["is_invoke"] is True


class TestMessageExtensionSetting:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_setting_selector(self):
        @self.ext.message_extensions.setting()
        async def handler(ctx, state, settings): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(ActivityTypes.invoke, name="composeExtension/setting")
            )
            is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="composeExtension/query"))
            is False
        )

    def test_setting_is_invoke(self):
        @self.ext.message_extensions.setting()
        async def handler(ctx, state, settings): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_setting_always_sends_empty_response(self):
        @self.ext.message_extensions.setting()
        async def handler(ctx, state, settings): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="composeExtension/setting", value={}
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_awaited_once_with(ctx, None)


class TestMessageExtensionCardButtonClicked:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_card_button_clicked_selector(self):
        @self.ext.message_extensions.card_button_clicked()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke, name="composeExtension/onCardButtonClicked"
                )
            )
            is True
        )
        assert (
            selector(_make_context(ActivityTypes.invoke, name="composeExtension/query"))
            is False
        )

    def test_card_button_clicked_is_invoke(self):
        @self.ext.message_extensions.card_button_clicked()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True


class TestMessageExtensionDirectDecoratorStyle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_select_item_direct(self):
        @self.ext.message_extensions.select_item  # type: ignore[arg-type]
        async def handler(ctx, state, value): ...

        assert self.app._routes[0]["selector"] is not None

    def test_query_link_direct(self):
        @self.ext.message_extensions.query_link  # type: ignore[arg-type]
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["selector"] is not None

    def test_anonymous_query_link_direct(self):
        @self.ext.message_extensions.anonymous_query_link  # type: ignore[arg-type]
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["selector"] is not None

    def test_query_setting_url_direct(self):
        @self.ext.message_extensions.query_setting_url  # type: ignore[arg-type]
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["selector"] is not None

    def test_setting_direct(self):
        @self.ext.message_extensions.setting  # type: ignore[arg-type]
        async def handler(ctx, state, value): ...

        assert self.app._routes[0]["selector"] is not None

    def test_card_button_clicked_direct(self):
        @self.ext.message_extensions.card_button_clicked  # type: ignore[arg-type]
        async def handler(ctx, state, value): ...

        assert self.app._routes[0]["selector"] is not None


class TestMessageExtensionHandlerExecution:
    """Exercises the handler closures (payload parsing + response sending), not
    just the selectors, for the message-extension methods that lacked such tests."""

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    @pytest.mark.asyncio
    async def test_select_item_passes_raw_value_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.select_item()
        async def handler(ctx, state, value):
            return await user_handler(ctx, state, value)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/selectItem",
            value={"item": "42"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            # select_item forwards the raw, unvalidated value
            assert user_handler.call_args[0][2] == {"item": "42"}
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_select_item_skips_send_when_handler_returns_none(self):
        @self.ext.message_extensions.select_item()
        async def handler(ctx, state, value):
            return None

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="composeExtension/selectItem", value={}
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_submit_action_parses_action_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.submit_action()
        async def handler(ctx, state, action):
            return await user_handler(ctx, state, action)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "c", "commandContext": "compose"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], MessagingExtensionAction)
            mock_send.assert_awaited_once_with(ctx, response)

    def test_submit_action_selector_handles_non_dict_value(self):
        # The selector reads botMessagePreviewAction via getattr when value is an
        # object rather than a dict; a preview action must exclude this route.
        @self.ext.message_extensions.submit_action()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]

        preview_value = SimpleNamespace(botMessagePreviewAction="edit", commandId="c")
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value=preview_value,
                )
            )
            is False
        )

        non_preview_value = SimpleNamespace(botMessagePreviewAction=None, commandId="c")
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="composeExtension/submitAction",
                    value=non_preview_value,
                )
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_fetch_action_parses_action_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.fetch_action()
        async def handler(ctx, state, action):
            return await user_handler(ctx, state, action)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/fetchTask",
            value={"commandId": "c", "commandContext": "compose"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], MessagingExtensionAction)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_query_link_parses_query_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.query_link()
        async def handler(ctx, state, query):
            return await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/queryLink",
            value={"url": "https://example.com"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], AppBasedLinkQuery)
            assert user_handler.call_args[0][2].url == "https://example.com"
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_anonymous_query_link_parses_query_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.anonymous_query_link()
        async def handler(ctx, state, query):
            return await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/anonymousQueryLink",
            value={"url": "https://example.com"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], AppBasedLinkQuery)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_query_setting_url_parses_query_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.message_extensions.query_setting_url()
        async def handler(ctx, state, query):
            return await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/querySettingUrl",
            value={"commandId": "c"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], MessagingExtensionQuery)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_card_button_clicked_forwards_value_and_sends_empty_response(self):
        user_handler = AsyncMock()

        @self.ext.message_extensions.card_button_clicked()
        async def handler(ctx, state, value):
            await user_handler(ctx, state, value)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/onCardButtonClicked",
            value={"id": "btn-1"},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            # raw value is forwarded; an empty invoke response is always sent
            assert user_handler.call_args[0][2] == {"id": "btn-1"}
            mock_send.assert_awaited_once_with(ctx)
