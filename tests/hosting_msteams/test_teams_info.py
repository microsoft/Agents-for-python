# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for TeamsInfo."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_teams.api.models import (
        ChannelData,
        ChannelInfo,
        MeetingInfo,
        MeetingParticipant,
        PagedMembersResult,
        TeamsChannelAccount,
        TeamDetails,
    )
    from microsoft_agents.activity import Activity, ChannelAccount
    from microsoft_agents.hosting.core import TurnContext
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


def _make_api_client():
    """Build a mock ApiClient with meetings/teams/conversations sub-objects."""
    members_proxy = MagicMock()
    members_proxy.get_paged = AsyncMock()
    members_proxy.get = AsyncMock()

    api_client = MagicMock()
    api_client.meetings = MagicMock()
    api_client.meetings.get_participant = AsyncMock()
    api_client.meetings.get_by_id = AsyncMock()
    api_client.teams = MagicMock()
    api_client.teams.get_by_id = AsyncMock()
    api_client.teams.get_conversations = AsyncMock()
    api_client.conversations = MagicMock()
    api_client.conversations.members = MagicMock(return_value=members_proxy)
    return api_client


def _make_context(channel_data=None, api_client=None) -> "TurnContext":
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
    context.activity = activity
    context.turn_state = {"TeamsApiClient": api_client}
    context.adapter = MagicMock()
    return context


_PATCH_TARGET = "microsoft_agents.hosting.teams.teams_info.get_cached_teams_api_client"


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


# --- get_meeting_participant ---


class TestGetMeetingParticipant:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_params(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=MeetingParticipant)
        api_client.meetings.get_participant.return_value = expected

        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_meeting_participant(
                context, meeting_id="m1", participant_id="p1", tenant_id="t1"
            )

        api_client.meetings.get_participant.assert_called_once_with("m1", "p1", "t1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_extracts_params_from_activity(self):
        api_client = _make_api_client()
        api_client.meetings.get_participant.return_value = MagicMock()

        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, api_client)
        context.activity.from_property.aad_object_id = "aad-user"

        with patch(_PATCH_TARGET, return_value=api_client):
            await TeamsInfo.get_meeting_participant(context)

        api_client.meetings.get_participant.assert_called_once_with(
            "m1", "aad-user", "t1"
        )

    @pytest.mark.asyncio
    async def test_raises_if_participant_id_missing(self):
        api_client = _make_api_client()
        channel_data = _make_channel_data(tenant_id="t1", meeting_id="m1")
        context = _make_context(channel_data, api_client)
        context.activity.from_property.aad_object_id = None

        with patch(_PATCH_TARGET, return_value=api_client):
            with pytest.raises(ValueError, match="participant_id"):
                await TeamsInfo.get_meeting_participant(context)


# --- get_meeting_info ---


class TestGetMeetingInfo:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_meeting_id(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=MeetingInfo)
        api_client.meetings.get_by_id.return_value = expected

        channel_data = _make_channel_data(meeting_id="m1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_meeting_info(context, "m1")

        api_client.meetings.get_by_id.assert_called_once_with("m1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_meeting_id(self):
        api_client = _make_api_client()
        api_client.meetings.get_by_id.return_value = MagicMock()

        channel_data = _make_channel_data(meeting_id="from-data")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            await TeamsInfo.get_meeting_info(context)

        api_client.meetings.get_by_id.assert_called_once_with("from-data")


# --- get_team_details ---


class TestGetTeamDetails:
    @pytest.mark.asyncio
    async def test_calls_client_with_explicit_team_id(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=TeamDetails)
        api_client.teams.get_by_id.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_team_details(context, "team1")

        api_client.teams.get_by_id.assert_called_once_with("team1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_team_id(self):
        api_client = _make_api_client()
        api_client.teams.get_by_id.return_value = MagicMock()

        channel_data = _make_channel_data(team_id="team-from-data")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            await TeamsInfo.get_team_details(context)

        api_client.teams.get_by_id.assert_called_once_with("team-from-data")


# --- get_team_channels ---


class TestGetTeamChannels:
    @pytest.mark.asyncio
    async def test_calls_client_with_team_id(self):
        api_client = _make_api_client()
        expected = [MagicMock(spec=ChannelInfo)]
        api_client.teams.get_conversations.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_team_channels(context, "team1")

        api_client.teams.get_conversations.assert_called_once_with("team1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_channel_data_team_id(self):
        api_client = _make_api_client()
        api_client.teams.get_conversations.return_value = []

        channel_data = _make_channel_data(team_id="team-from-data")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            await TeamsInfo.get_team_channels(context)

        api_client.teams.get_conversations.assert_called_once_with("team-from-data")


# --- get_paged_members ---


class TestGetPagedMembers:
    @pytest.mark.asyncio
    async def test_uses_team_id_when_present(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=PagedMembersResult)
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get_paged.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_paged_members(context)

        api_client.conversations.members.assert_called_once_with("team1")
        members_proxy.get_paged.assert_called_once_with(None, "")
        assert result is expected

    @pytest.mark.asyncio
    async def test_falls_back_to_conversation_id_when_no_team(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=PagedMembersResult)
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get_paged.return_value = expected

        channel_data = _make_channel_data()  # no team_id
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_paged_members(context)

        api_client.conversations.members.assert_called_once_with("conv-id")
        assert result is expected

    @pytest.mark.asyncio
    async def test_passes_page_size_and_continuation_token(self):
        api_client = _make_api_client()
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get_paged.return_value = MagicMock(spec=PagedMembersResult)

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            await TeamsInfo.get_paged_members(
                context, page_size=10, continuation_token="tok"
            )

        members_proxy.get_paged.assert_called_once_with(10, "tok")


# --- get_team_member ---


class TestGetTeamMember:
    @pytest.mark.asyncio
    async def test_calls_client_with_team_and_user_id(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=TeamsChannelAccount)
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get.return_value = expected

        context = _make_context(api_client=api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_team_member(context, "team1", "user1")

        api_client.conversations.members.assert_called_once_with("team1")
        members_proxy.get.assert_called_once_with("user1")
        assert result is expected


# --- get_member ---


class TestGetMember:
    @pytest.mark.asyncio
    async def test_routes_to_get_team_member_when_team_id_set(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=TeamsChannelAccount)
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get.return_value = expected

        channel_data = _make_channel_data(team_id="team1")
        context = _make_context(channel_data, api_client)

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_member(context, "user1")

        api_client.conversations.members.assert_called_once_with("team1")
        members_proxy.get.assert_called_once_with("user1")
        assert result is expected

    @pytest.mark.asyncio
    async def test_routes_to_conversation_when_no_team_id(self):
        api_client = _make_api_client()
        expected = MagicMock(spec=TeamsChannelAccount)
        members_proxy = api_client.conversations.members.return_value
        members_proxy.get.return_value = expected

        channel_data = _make_channel_data()  # no team_id
        context = _make_context(channel_data, api_client)
        context.activity.conversation.id = "conv-id"

        with patch(_PATCH_TARGET, return_value=api_client):
            result = await TeamsInfo.get_member(context, "user1")

        api_client.conversations.members.assert_called_once_with("conv-id")
        members_proxy.get.assert_called_once_with("user1")
        assert result is expected
