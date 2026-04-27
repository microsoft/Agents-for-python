"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import re
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import Activity, ActivityTypes, InvokeResponse
from microsoft_agents.activity.teams import (
    AppBasedLinkQuery,
    FileConsentCardResponse,
    MeetingEndEventDetails,
    MeetingParticipantsEventDetails,
    MeetingStartEventDetails,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    O365ConnectorCardActionQuery,
    ReadReceiptInfo,
    TaskModuleRequest,
    TaskModuleResponse,
)
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.teams import TeamsAgentExtension


def _make_app() -> AgentApplication:
    app = MagicMock(spec=AgentApplication)
    app._routes = []

    def _add_route(selector, handler, is_invoke=False, rank=RouteRank.DEFAULT, auth_handlers=None):
        app._routes.append(
            dict(
                selector=selector,
                handler=handler,
                is_invoke=is_invoke,
                rank=rank,
                auth_handlers=auth_handlers,
            )
        )

    app.add_route.side_effect = _add_route
    return app


def _make_context(
    activity_type: str,
    name: str = None,
    value: dict = None,
    channel_id: str = "msteams",
    channel_data: dict = None,
    members_added=None,
    members_removed=None,
) -> TurnContext:
    context = MagicMock(spec=TurnContext)
    activity = MagicMock(spec=Activity)
    activity.type = activity_type
    activity.name = name
    activity.value = value
    activity.channel_id = channel_id
    activity.channel_data = channel_data
    activity.members_added = members_added
    activity.members_removed = members_removed
    context.activity = activity
    context.send_activity = AsyncMock()
    return context


class TestTaskModule:

    def setup_method(self):
        self.app = _make_app()
        self.teams = TeamsAgentExtension(self.app)

    # ── Selector tests ──────────────────────────────────────────────────────

    def test_on_fetch_no_verb_matches_any(self):
        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="task/fetch", value={})
        assert selector(ctx) is True

    def test_on_fetch_verb_matches_exact(self):
        @self.teams.task_module.on_fetch("myVerb")
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx_match = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": {"verb": "myVerb"}}
        )
        ctx_no_match = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": {"verb": "otherVerb"}}
        )
        assert selector(ctx_match) is True
        assert selector(ctx_no_match) is False

    def test_on_fetch_verb_matches_regex(self):
        @self.teams.task_module.on_fetch(re.compile(r"my.*"))
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx_match = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": {"verb": "mySpecialVerb"}}
        )
        ctx_no_match = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": {"verb": "otherVerb"}}
        )
        assert selector(ctx_match) is True
        assert selector(ctx_no_match) is False

    def test_on_fetch_wrong_invoke_name(self):
        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="task/submit", value={})
        assert selector(ctx) is False

    def test_on_fetch_wrong_activity_type(self):
        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.message, name="task/fetch")
        assert selector(ctx) is False

    def test_on_submit_selector(self):
        @self.teams.task_module.on_submit("submitVerb")
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx_match = _make_context(
            ActivityTypes.invoke, name="task/submit",
            value={"data": {"verb": "submitVerb"}}
        )
        ctx_no_match = _make_context(
            ActivityTypes.invoke, name="task/submit",
            value={"data": {"verb": "other"}}
        )
        assert selector(ctx_match) is True
        assert selector(ctx_no_match) is False

    def test_on_fetch_is_invoke(self):
        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_on_submit_is_invoke(self):
        @self.teams.task_module.on_submit()
        async def handler(ctx, state, req): ...

        assert self.app._routes[0]["is_invoke"] is True

    # ── Handler tests ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_on_fetch_handler_passes_request_and_sends_response(self):
        response = TaskModuleResponse()
        user_handler = AsyncMock(return_value=response)

        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req: TaskModuleRequest):
            return await user_handler(ctx, state, req)

        route_handler = self.app._routes[0]["handler"]
        state = MagicMock()
        ctx = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": {"verb": "myVerb"}, "context": None}
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await route_handler(ctx, state)
            assert user_handler.called
            args = user_handler.call_args[0]
            assert isinstance(args[2], TaskModuleRequest)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_on_fetch_handler_skips_send_when_none_returned(self):
        @self.teams.task_module.on_fetch()
        async def handler(ctx, state, req): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="task/fetch",
            value={"data": None, "context": None}
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_not_awaited()


class TestMessageExtension:

    def setup_method(self):
        self.app = _make_app()
        self.teams = TeamsAgentExtension(self.app)

    def test_on_query_matches_by_command_id(self):
        @self.teams.message_extension.on_query("searchCmd")
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        ctx_match = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/query",
            value={"commandId": "searchCmd"},
        )
        ctx_no_match = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/query",
            value={"commandId": "otherCmd"},
        )
        assert selector(ctx_match) is True
        assert selector(ctx_no_match) is False

    def test_on_query_no_command_id_matches_all(self):
        @self.teams.message_extension.on_query()
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/query",
            value={"commandId": "anyCommand"},
        )
        assert selector(ctx) is True

    def test_on_query_is_invoke(self):
        @self.teams.message_extension.on_query()
        async def handler(ctx, state, query): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_on_submit_action_excludes_preview(self):
        @self.teams.message_extension.on_submit_action()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        ctx_normal = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd"},
        )
        ctx_preview = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
        )
        assert selector(ctx_normal) is True
        assert selector(ctx_preview) is False

    def test_on_agent_message_preview_edit_selector(self):
        @self.teams.message_extension.on_agent_message_preview_edit()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        ctx_edit = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
        )
        ctx_send = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "send"},
        )
        assert selector(ctx_edit) is True
        assert selector(ctx_send) is False

    def test_on_agent_message_preview_send_selector(self):
        @self.teams.message_extension.on_agent_message_preview_send()
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        ctx_send = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "send"},
        )
        ctx_edit = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/submitAction",
            value={"commandId": "cmd", "botMessagePreviewAction": "edit"},
        )
        assert selector(ctx_send) is True
        assert selector(ctx_edit) is False

    def test_on_fetch_task_matches_command_id(self):
        @self.teams.message_extension.on_fetch_task("myCmd")
        async def handler(ctx, state, action): ...

        selector = self.app._routes[0]["selector"]
        ctx_match = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/fetchTask",
            value={"commandId": "myCmd"},
        )
        ctx_no_match = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/fetchTask",
            value={"commandId": "other"},
        )
        assert selector(ctx_match) is True
        assert selector(ctx_no_match) is False

    def test_on_query_link_selector(self):
        @self.teams.message_extension.on_query_link
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="composeExtension/queryLink")
        ctx_other = _make_context(ActivityTypes.invoke, name="composeExtension/query")
        assert selector(ctx) is True
        assert selector(ctx_other) is False

    def test_on_anonymous_query_link_selector(self):
        @self.teams.message_extension.on_anonymous_query_link
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="composeExtension/anonymousQueryLink")
        assert selector(ctx) is True

    def test_on_select_item_selector(self):
        @self.teams.message_extension.on_select_item
        async def handler(ctx, state, item): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="composeExtension/selectItem")
        ctx_other = _make_context(ActivityTypes.invoke, name="composeExtension/query")
        assert selector(ctx) is True
        assert selector(ctx_other) is False

    def test_on_configure_settings_sends_empty_response(self):
        """on_configure_settings always sends a 200 regardless of handler return value."""

        @self.teams.message_extension.on_configure_settings
        async def handler(ctx, state, settings): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_on_card_button_clicked_selector(self):
        @self.teams.message_extension.on_card_button_clicked
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="composeExtension/onCardButtonClicked")
        assert selector(ctx) is True

    @pytest.mark.asyncio
    async def test_on_query_handler_parses_query_and_sends_response(self):
        response = MessagingExtensionResponse()
        user_handler = AsyncMock(return_value=response)

        @self.teams.message_extension.on_query()
        async def handler(ctx, state, query: MessagingExtensionQuery):
            return await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="composeExtension/query",
            value={"commandId": "search"},
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await route_handler(ctx, MagicMock())
            args = user_handler.call_args[0]
            assert isinstance(args[2], MessagingExtensionQuery)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_on_configure_settings_always_sends_response(self):
        @self.teams.message_extension.on_configure_settings
        async def handler(ctx, state, settings): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke, name="composeExtension/setting", value={}
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_awaited_once_with(ctx)


class TestMeeting:

    def setup_method(self):
        self.app = _make_app()
        self.teams = TeamsAgentExtension(self.app)

    def test_on_start_selector(self):
        @self.teams.meeting.on_start
        async def handler(ctx, state, meeting): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.event, name="application/vnd.microsoft.meetingStart")
        ctx_other = _make_context(ActivityTypes.event, name="application/vnd.microsoft.meetingEnd")
        assert selector(ctx) is True
        assert selector(ctx_other) is False

    def test_on_end_selector(self):
        @self.teams.meeting.on_end
        async def handler(ctx, state, meeting): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.event, name="application/vnd.microsoft.meetingEnd")
        assert selector(ctx) is True

    def test_on_participants_join_selector(self):
        @self.teams.meeting.on_participants_join
        async def handler(ctx, state, details): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingParticipantJoin",
        )
        assert selector(ctx) is True

    def test_on_participants_leave_selector(self):
        @self.teams.meeting.on_participants_leave
        async def handler(ctx, state, details): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingParticipantLeave",
        )
        assert selector(ctx) is True

    def test_on_start_is_not_invoke(self):
        @self.teams.meeting.on_start
        async def handler(ctx, state, meeting): ...

        assert self.app._routes[0]["is_invoke"] is False

    @pytest.mark.asyncio
    async def test_on_start_handler_parses_meeting_details(self):
        user_handler = AsyncMock()

        @self.teams.meeting.on_start
        async def handler(ctx, state, meeting: MeetingStartEventDetails):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingStart",
            value={},
        )
        await route_handler(ctx, MagicMock())
        args = user_handler.call_args[0]
        assert isinstance(args[2], MeetingStartEventDetails)

    @pytest.mark.asyncio
    async def test_on_end_handler_parses_meeting_details(self):
        user_handler = AsyncMock()

        @self.teams.meeting.on_end
        async def handler(ctx, state, meeting: MeetingEndEventDetails):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingEnd",
            value={},
        )
        await route_handler(ctx, MagicMock())
        args = user_handler.call_args[0]
        assert isinstance(args[2], MeetingEndEventDetails)

    @pytest.mark.asyncio
    async def test_on_participants_join_handler_parses_details(self):
        user_handler = AsyncMock()

        @self.teams.meeting.on_participants_join
        async def handler(ctx, state, details: MeetingParticipantsEventDetails):
            await user_handler(ctx, state, details)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingParticipantJoin",
            value={},
        )
        await route_handler(ctx, MagicMock())
        args = user_handler.call_args[0]
        assert isinstance(args[2], MeetingParticipantsEventDetails)


class TestTeamsAgentExtensionTopLevel:

    def setup_method(self):
        self.app = _make_app()
        self.teams = TeamsAgentExtension(self.app)

    # ── Message edit / undelete / soft delete ───────────────────────────────

    def test_on_message_edit_selector(self):
        @self.teams.on_message_edit
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.message_update,
            channel_data={"eventType": "editMessage"},
        )
        assert selector(ctx) is True

    def test_on_message_edit_wrong_event_type(self):
        @self.teams.on_message_edit
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.message_update,
            channel_data={"eventType": "undeleteMessage"},
        )
        assert selector(ctx) is False

    def test_on_message_edit_wrong_channel(self):
        @self.teams.on_message_edit
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.message_update,
            channel_id="webchat",
            channel_data={"eventType": "editMessage"},
        )
        assert selector(ctx) is False

    def test_on_message_undelete_selector(self):
        @self.teams.on_message_undelete
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.message_update,
            channel_data={"eventType": "undeleteMessage"},
        )
        assert selector(ctx) is True

    def test_on_message_soft_delete_selector(self):
        @self.teams.on_message_soft_delete
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.message_delete,
            channel_data={"eventType": "softDeleteMessage"},
        )
        assert selector(ctx) is True

    # ── Read receipt ───────────────────────────────────────────────────────

    def test_on_read_receipt_selector(self):
        @self.teams.on_read_receipt
        async def handler(ctx, state, receipt): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.event, name="application/vnd.microsoft.readReceipt")
        assert selector(ctx) is True

    @pytest.mark.asyncio
    async def test_on_read_receipt_handler_parses_receipt(self):
        user_handler = AsyncMock()

        @self.teams.on_read_receipt
        async def handler(ctx, state, receipt: ReadReceiptInfo):
            await user_handler(ctx, state, receipt)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.readReceipt",
            value={},
        )
        await route_handler(ctx, MagicMock())
        args = user_handler.call_args[0]
        assert isinstance(args[2], ReadReceiptInfo)

    # ── Config ─────────────────────────────────────────────────────────────

    def test_on_config_fetch_selector(self):
        @self.teams.on_config_fetch
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="config/fetch")
        ctx_other = _make_context(ActivityTypes.invoke, name="config/submit")
        assert selector(ctx) is True
        assert selector(ctx_other) is False

    def test_on_config_fetch_is_invoke(self):
        @self.teams.on_config_fetch
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is True

    def test_on_config_submit_selector(self):
        @self.teams.on_config_submit
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="config/submit")
        assert selector(ctx) is True

    # ── File consent ───────────────────────────────────────────────────────

    def test_on_file_consent_accept_selector(self):
        @self.teams.on_file_consent_accept
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        ctx_accept = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "accept"},
        )
        ctx_decline = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "decline"},
        )
        assert selector(ctx_accept) is True
        assert selector(ctx_decline) is False

    def test_on_file_consent_decline_selector(self):
        @self.teams.on_file_consent_decline
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        ctx_decline = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "decline"},
        )
        ctx_accept = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "accept"},
        )
        assert selector(ctx_decline) is True
        assert selector(ctx_accept) is False

    @pytest.mark.asyncio
    async def test_on_file_consent_accept_sends_empty_response(self):
        @self.teams.on_file_consent_accept
        async def handler(ctx, state, data): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="fileConsent/invoke",
            value={"action": "accept", "context": None, "uploadInfo": None},
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_awaited_once_with(ctx)

    # ── O365 ───────────────────────────────────────────────────────────────

    def test_on_o365_connector_card_action_selector(self):
        @self.teams.on_o365_connector_card_action
        async def handler(ctx, state, query): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="actionableMessage/executeAction")
        assert selector(ctx) is True

    @pytest.mark.asyncio
    async def test_on_o365_connector_card_action_parses_query(self):
        user_handler = AsyncMock()

        @self.teams.on_o365_connector_card_action
        async def handler(ctx, state, query: O365ConnectorCardActionQuery):
            await user_handler(ctx, state, query)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="actionableMessage/executeAction",
            value={},
        )
        with patch(
            "microsoft_agents.hosting.teams.teams_agent_extension._send_invoke_response",
            new_callable=AsyncMock,
        ):
            await route_handler(ctx, MagicMock())
        args = user_handler.call_args[0]
        assert isinstance(args[2], O365ConnectorCardActionQuery)

    # ── Conversation update events ─────────────────────────────────────────

    def test_on_members_added_selector(self):
        @self.teams.on_members_added
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        ctx = _make_context(
            ActivityTypes.conversation_update,
            members_added=[member],
        )
        ctx_empty = _make_context(
            ActivityTypes.conversation_update,
            members_added=[],
        )
        assert selector(ctx) is True
        assert selector(ctx_empty) is False

    def test_on_members_added_requires_teams_channel(self):
        @self.teams.on_members_added
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_id="webchat",
            members_added=[member],
        )
        assert selector(ctx) is False

    def test_on_members_removed_selector(self):
        @self.teams.on_members_removed
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        ctx = _make_context(
            ActivityTypes.conversation_update,
            members_removed=[member],
        )
        assert selector(ctx) is True

    def test_on_channel_created_selector(self):
        @self.teams.on_channel_created
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelCreated"},
        )
        ctx_other = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelDeleted"},
        )
        assert selector(ctx) is True
        assert selector(ctx_other) is False

    def test_on_channel_deleted_selector(self):
        @self.teams.on_channel_deleted
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelDeleted"},
        )
        assert selector(ctx) is True

    def test_on_channel_renamed_selector(self):
        @self.teams.on_channel_renamed
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelRenamed"},
        )
        assert selector(ctx) is True

    def test_on_channel_restored_selector(self):
        @self.teams.on_channel_restored
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelRestored"},
        )
        assert selector(ctx) is True

    def test_on_team_archived_selector(self):
        @self.teams.on_team_archived
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamArchived"},
        )
        assert selector(ctx) is True

    def test_on_team_deleted_selector(self):
        @self.teams.on_team_deleted
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamDeleted"},
        )
        assert selector(ctx) is True

    def test_on_team_hard_deleted_selector(self):
        @self.teams.on_team_hard_deleted
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamHardDeleted"},
        )
        assert selector(ctx) is True

    def test_on_team_renamed_selector(self):
        @self.teams.on_team_renamed
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamRenamed"},
        )
        assert selector(ctx) is True

    def test_on_team_restored_selector(self):
        @self.teams.on_team_restored
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamRestored"},
        )
        assert selector(ctx) is True

    def test_on_team_unarchived_selector(self):
        @self.teams.on_team_unarchived
        async def handler(ctx, state): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamUnarchived"},
        )
        assert selector(ctx) is True

    # ── Sub-object accessors ────────────────────────────────────────────────

    def test_properties_return_sub_objects(self):
        from microsoft_agents.hosting.teams.teams_agent_extension import (
            MessageExtension,
            TaskModule,
            Meeting,
        )

        assert isinstance(self.teams.message_extension, MessageExtension)
        assert isinstance(self.teams.task_module, TaskModule)
        assert isinstance(self.teams.meeting, Meeting)

    # ── Decorator style without args ────────────────────────────────────────

    def test_on_message_edit_direct_decorator(self):
        """Verify on_message_edit works as @teams.on_message_edit (no call parens)."""

        @self.teams.on_message_edit
        async def handler(ctx, state): ...

        assert len(self.app._routes) == 1

    def test_on_message_edit_factory_decorator(self):
        """Verify on_message_edit works as @teams.on_message_edit() (with call parens)."""

        @self.teams.on_message_edit()
        async def handler(ctx, state): ...

        assert len(self.app._routes) == 1
