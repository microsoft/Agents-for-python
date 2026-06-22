# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for TeamsInfo."""

import sys
import pytest
from unittest.mock import AsyncMock, MagicMock

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_teams.api.models.channel_data import ChannelData
    from microsoft_agents.activity import (
        Activity,
        ActivityTypes,
        ChannelAccount,
        ConversationAccount,
    )
    from microsoft_agents.hosting.core import TurnContext, ChannelServiceAdapter
    from microsoft_agents.hosting.core.connector.teams import TeamsConnectorClient
    from microsoft_agents.activity.teams import (
        TeamsChannelAccount,
        TeamsMeetingParticipant,
        MeetingInfo,
        TeamDetails,
        TeamsPagedMembersResult,
        MeetingNotification,
        MeetingNotificationResponse,
        TeamsMember,
        BatchOperationStateResponse,
        BatchFailedEntriesResponse,
        CancelOperationResponse,
        TeamsBatchOperationResponse,
        ChannelInfo,
    )
    from microsoft_agents.hosting.teams.teams_info import TeamsInfo


# --- helpers ---


def _make_channel_data(team_id=None, tenant_id=None, meeting_id=None) -> "ChannelData":
    data = {}
    if team_id:
        data["team"] = {"id": team_id}
    if tenant_id:
        data["tenant"] = {"id": tenant_id}
    if meeting_id:
        data["meeting"] = {"id": meeting_id}
    return ChannelData.model_validate(data)


def _make_context(channel_data=None, mock_client=None) -> "TurnContext":
    context = MagicMock(spec=TurnContext)
    activity = MagicMock(spec=Activity)
    activity.channel_data = channel_data
    from_prop = MagicMock()
    from_prop.aad_object_id = "user-aad-id"
    activity.from_property = from_prop
    conversation = MagicMock()
    conversation.id = "conv-id"
    activity.conversation = conversation
    activity.recipient = MagicMock(spec=ChannelAccount)
    activity.service_url = "https://example.com"
    activity.id = "activity-id"
    activity.get_conversation_reference = MagicMock(
        return_value=MagicMock(conversation=MagicMock())
    )
    context.activity = activity
    context.turn_state = {"ConnectorClient": mock_client}
    context.adapter = MagicMock()
    return context


# --- _get_meeting_id ---


class TestGetMeetingIdHelper:
    def test_returns_explicit_meeting_id(self):
        channel_data = _make_channel_data()
        assert TeamsInfo._get_meeting_id(channel_data, "explicit-id") == "explicit-id"

    def test_falls_back_to_channel_data_meeting(self):
        channel_data = _make_channel_data(meeting_id="from-data")
        assert TeamsInfo._get_meeting_id(channel_data) == "from-data"

    def test_raises_if_both_missing(self):
        channel_data = _make_channel_data()
        with pytest.raises(ValueError, match="meeting_id"):
            TeamsInfo._get_meeting_id(channel_data)


# --- _get_tenant_id ---


class TestGetTenantIdHelper:
    def test_returns_explicit_tenant_id(self):
        channel_data = _make_channel_data()
        assert (
            TeamsInfo._get_tenant_id(channel_data, "explicit-tenant")
            == "explicit-tenant"
        )

    def test_falls_back_to_channel_data_tenant(self):
        channel_data = _make_channel_data(tenant_id="tenant-from-data")
        assert TeamsInfo._get_tenant_id(channel_data) == "tenant-from-data"

    def test_raises_if_both_missing(self):
        channel_data = _make_channel_data()
        with pytest.raises(ValueError, match="tenant_id"):
            TeamsInfo._get_tenant_id(channel_data)


# --- _get_team_id ---


class TestGetTeamIdHelper:
    def test_returns_explicit_team_id(self):
        channel_data = _make_channel_data()
        assert TeamsInfo._get_team_id(channel_data, "explicit-team") == "explicit-team"

    def test_falls_back_to_channel_data_team(self):
        channel_data = _make_channel_data(team_id="team-from-data")
        assert TeamsInfo._get_team_id(channel_data) == "team-from-data"

    def test_raises_if_both_missing(self):
        channel_data = _make_channel_data()
        with pytest.raises(ValueError, match="team_id"):
            TeamsInfo._get_team_id(channel_data)


# --- _get_rest_client ---


class TestGetRestClient:
    def test_returns_client_from_turn_state(self):
        mock_client = MagicMock(spec=TeamsConnectorClient)
        context = _make_context(mock_client=mock_client)
        assert TeamsInfo._get_rest_client(context) is mock_client

    def test_raises_if_client_missing(self):
        context = _make_context(mock_client=None)
        with pytest.raises(ValueError, match="TeamsConnectorClient"):
            TeamsInfo._get_rest_client(context)


# --- get_meeting_participant ---


class TestGetMeetingParticipant:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_params(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsMeetingParticipant)
        mock_client.fetch_meeting_participant.return_value = expected

        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_meeting_participant(
            context, meeting_id="m1", participant_id="p1", tenant_id="t1"
        )

        mock_client.fetch_meeting_participant.assert_called_once_with("m1", "p1", "t1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_extracts_params_from_activity(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        mock_client.fetch_meeting_participant.return_value = MagicMock()

        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, mock_client)
        context.activity.from_property.aad_object_id = "aad-user"

        await TeamsInfo.get_meeting_participant(context)

        mock_client.fetch_meeting_participant.assert_called_once_with(
            "m1", "aad-user", "t1"
        )

    @pytest.mark.asyncio
    async def test_raises_if_participant_id_missing(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, mock_client)
        context.activity.from_property.aad_object_id = None

        with pytest.raises(ValueError, match="participant_id"):
            await TeamsInfo.get_meeting_participant(context)


# --- get_meeting_info ---


class TestGetMeetingInfo:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_meeting_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=MeetingInfo)
        mock_client.fetch_meeting_info.return_value = expected

        channel_data = _make_channel_data(meeting_id="m1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_meeting_info(context, "m1")

        mock_client.fetch_meeting_info.assert_called_once_with("m1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_meeting_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        mock_client.fetch_meeting_info.return_value = MagicMock()

        channel_data = _make_channel_data(meeting_id="from-data")
        context = _make_context(channel_data, mock_client)

        await TeamsInfo.get_meeting_info(context)

        mock_client.fetch_meeting_info.assert_called_once_with("from-data")


# --- get_team_details ---


class TestGetTeamDetails:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_team_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamDetails)
        mock_client.fetch_team_details.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_team_details(context, "team1")

        mock_client.fetch_team_details.assert_called_once_with("team1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_team_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        mock_client.fetch_team_details.return_value = MagicMock()

        channel_data = _make_channel_data(team_id="team-from-data")
        context = _make_context(channel_data, mock_client)

        await TeamsInfo.get_team_details(context)

        mock_client.fetch_team_details.assert_called_once_with("team-from-data")


# --- send_message_to_teams_channel ---


class TestSendMessageToTeamsChannel:
    @pytest.mark.asyncio
    async def test_uses_connector_client_when_no_app_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        resource_response = MagicMock()
        resource_response.id = "new-conv-id"
        resource_response.activity_id = "new-act-id"
        mock_client.conversations = AsyncMock()
        mock_client.conversations.create_conversation = AsyncMock(
            return_value=resource_response
        )

        channel_data = _make_channel_data()
        context = _make_context(channel_data, mock_client)
        activity = Activity(type=ActivityTypes.message, text="hello")

        conv_ref, act_id = await TeamsInfo.send_message_to_teams_channel(
            context, activity, "channel-id"
        )

        mock_client.conversations.create_conversation.assert_called_once()
        assert act_id == "new-act-id"

    @pytest.mark.asyncio
    async def test_uses_adapter_when_app_id_and_channel_service_adapter(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        channel_data = _make_channel_data()
        context = _make_context(channel_data, mock_client)

        mock_adapter = MagicMock()
        mock_adapter.__class__ = ChannelServiceAdapter
        mock_adapter.create_conversation = AsyncMock()
        context.adapter = mock_adapter

        activity = Activity(type=ActivityTypes.message, text="hello")

        await TeamsInfo.send_message_to_teams_channel(
            context, activity, "channel-id", app_id="app-123"
        )

        mock_adapter.create_conversation.assert_called_once()
        mock_client.conversations.create_conversation.assert_not_called()


# --- get_team_channels ---


class TestGetTeamChannels:
    @pytest.mark.asyncio
    async def test_calls_client_with_team_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = [MagicMock(spec=ChannelInfo)]
        mock_client.fetch_channel_list.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_team_channels(context, "team1")

        mock_client.fetch_channel_list.assert_called_once_with("team1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_team_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        mock_client.fetch_channel_list.return_value = []

        channel_data = _make_channel_data(team_id="team-from-data")
        context = _make_context(channel_data, mock_client)

        await TeamsInfo.get_team_channels(context)

        mock_client.fetch_channel_list.assert_called_once_with("team-from-data")


# --- get_paged_members ---


class TestGetPagedMembers:
    @pytest.mark.asyncio
    async def test_routes_to_team_paged_members_when_team_set(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        page_result = MagicMock(spec=TeamsPagedMembersResult)
        page_result.members = []
        page_result.continuation_token = None
        mock_client.get_conversation_paged_member.return_value = page_result

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_paged_members(context)

        mock_client.get_conversation_paged_member.assert_called_once_with(
            "team1", 16, ""
        )
        assert result is page_result


# --- get_paged_team_members ---


class TestGetPagedTeamMembers:
    @pytest.mark.asyncio
    async def test_returns_single_page_result(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        page_result = MagicMock(spec=TeamsPagedMembersResult)
        page_result.members = [MagicMock(), MagicMock()]
        page_result.continuation_token = None
        mock_client.get_conversation_paged_member.return_value = page_result

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_paged_team_members(context)

        mock_client.get_conversation_paged_member.assert_called_once()
        assert result is page_result

    @pytest.mark.asyncio
    async def test_aggregates_multiple_pages(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        page1 = MagicMock(spec=TeamsPagedMembersResult)
        page1.members = [MagicMock()]
        page1.continuation_token = "token1"

        page2 = MagicMock(spec=TeamsPagedMembersResult)
        page2.members = [MagicMock()]
        page2.continuation_token = None

        mock_client.get_conversation_paged_member.side_effect = [page1, page2]

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_paged_team_members(context)

        assert mock_client.get_conversation_paged_member.call_count == 2
        assert len(result.members) == 2


# --- get_team_member ---


class TestGetTeamMember:
    @pytest.mark.asyncio
    async def test_calls_client_with_team_and_user_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsChannelAccount)
        mock_client.get_conversation_member.return_value = expected

        context = _make_context(mock_client=mock_client)

        result = await TeamsInfo.get_team_member(context, "team1", "user1")

        mock_client.get_conversation_member.assert_called_once_with("team1", "user1")
        assert result is expected


# --- get_member ---


class TestGetMember:
    @pytest.mark.asyncio
    async def test_routes_to_get_team_member_when_team_id_set(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsChannelAccount)
        mock_client.get_conversation_member.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, mock_client)

        result = await TeamsInfo.get_member(context, "user1")

        mock_client.get_conversation_member.assert_called_once_with("team1", "user1")
        assert result is expected


# --- send_meeting_notification ---


class TestSendMeetingNotification:
    @pytest.mark.asyncio
    async def test_calls_client_with_meeting_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=MeetingNotificationResponse)
        mock_client.send_meeting_notification.return_value = expected

        channel_data = _make_channel_data(meeting_id="m1")
        context = _make_context(channel_data, mock_client)
        notification = MagicMock(spec=MeetingNotification)

        result = await TeamsInfo.send_meeting_notification(context, notification)

        mock_client.send_meeting_notification.assert_called_once_with(
            "m1", notification
        )
        assert result is expected


# --- send_message_to_list_of_users ---


class TestSendMessageToListOfUsers:
    @pytest.mark.asyncio
    async def test_raises_if_members_empty(self):
        context = _make_context()
        activity = MagicMock(spec=Activity)
        with pytest.raises(ValueError, match="members"):
            await TeamsInfo.send_message_to_list_of_users(
                context, activity, "tenant1", []
            )

    @pytest.mark.asyncio
    async def test_calls_client_with_members(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsBatchOperationResponse)
        mock_client.send_message_to_list_of_users.return_value = expected

        context = _make_context(mock_client=mock_client)
        activity = MagicMock(spec=Activity)
        members = [MagicMock(spec=TeamsMember)]

        result = await TeamsInfo.send_message_to_list_of_users(
            context, activity, "tenant1", members
        )

        mock_client.send_message_to_list_of_users.assert_called_once_with(
            activity, "tenant1", members
        )
        assert result is expected


# --- send_message_to_all_users_in_tenant ---


class TestSendMessageToAllUsersInTenant:
    @pytest.mark.asyncio
    async def test_calls_client(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsBatchOperationResponse)
        mock_client.send_message_to_all_users_in_tenant.return_value = expected

        context = _make_context(mock_client=mock_client)
        activity = MagicMock(spec=Activity)

        result = await TeamsInfo.send_message_to_all_users_in_tenant(
            context, activity, "tenant1"
        )

        mock_client.send_message_to_all_users_in_tenant.assert_called_once_with(
            activity, "tenant1"
        )
        assert result is expected


# --- send_message_to_all_users_in_team ---


class TestSendMessageToAllUsersInTeam:
    @pytest.mark.asyncio
    async def test_calls_client(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsBatchOperationResponse)
        mock_client.send_message_to_all_users_in_team.return_value = expected

        context = _make_context(mock_client=mock_client)
        activity = MagicMock(spec=Activity)

        result = await TeamsInfo.send_message_to_all_users_in_team(
            context, activity, "tenant1", "team1"
        )

        mock_client.send_message_to_all_users_in_team.assert_called_once_with(
            activity, "tenant1", "team1"
        )
        assert result is expected


# --- send_message_to_list_of_channels ---


class TestSendMessageToListOfChannels:
    @pytest.mark.asyncio
    async def test_raises_if_members_empty(self):
        context = _make_context()
        activity = MagicMock(spec=Activity)
        with pytest.raises(ValueError, match="members"):
            await TeamsInfo.send_message_to_list_of_channels(
                context, activity, "tenant1", []
            )

    @pytest.mark.asyncio
    async def test_calls_client_with_members(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=TeamsBatchOperationResponse)
        mock_client.send_message_to_list_of_channels.return_value = expected

        context = _make_context(mock_client=mock_client)
        activity = MagicMock(spec=Activity)
        members = [MagicMock(spec=TeamsMember)]

        result = await TeamsInfo.send_message_to_list_of_channels(
            context, activity, "tenant1", members
        )

        mock_client.send_message_to_list_of_channels.assert_called_once_with(
            activity, "tenant1", members
        )
        assert result is expected


# --- get_operation_state ---


class TestGetOperationState:
    @pytest.mark.asyncio
    async def test_calls_client_with_operation_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=BatchOperationStateResponse)
        mock_client.get_operation_state.return_value = expected

        context = _make_context(mock_client=mock_client)

        result = await TeamsInfo.get_operation_state(context, "op1")

        mock_client.get_operation_state.assert_called_once_with("op1")
        assert result is expected


# --- get_failed_entries ---


class TestGetFailedEntries:
    @pytest.mark.asyncio
    async def test_calls_client_with_operation_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=BatchFailedEntriesResponse)
        mock_client.get_failed_entries.return_value = expected

        context = _make_context(mock_client=mock_client)

        result = await TeamsInfo.get_failed_entries(context, "op1")

        mock_client.get_failed_entries.assert_called_once_with("op1")
        assert result is expected


# --- cancel_operation ---


class TestCancelOperation:
    @pytest.mark.asyncio
    async def test_calls_client_with_operation_id(self):
        mock_client = AsyncMock(spec=TeamsConnectorClient)
        expected = MagicMock(spec=CancelOperationResponse)
        mock_client.cancel_operation.return_value = expected

        context = _make_context(mock_client=mock_client)

        result = await TeamsInfo.cancel_operation(context, "op1")

        mock_client.cancel_operation.assert_called_once_with("op1")
        assert result is expected
