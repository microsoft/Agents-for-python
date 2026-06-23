# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams information utilities for Microsoft Agents."""

from microsoft_teams.api.models import (
    ChannelData,
    ChannelInfo,
    MeetingInfo,
    MeetingParticipant,
    PagedMembersResult,
    TeamsChannelAccount,
    TeamDetails,
)

from microsoft_agents.hosting.core import TurnContext

from .errors import teams_errors
from ._teams_api_client import get_cached_teams_api_client
from ._utils import _get_channel_data


class TeamsInfo:
    """Teams information utilities for interacting with Teams-specific data."""

    @staticmethod
    def _get_meeting_id(
        channel_data: ChannelData, meeting_id: str | None = None
    ) -> str:
        if not meeting_id:
            meeting_id = getattr(channel_data.meeting, "id", None)
            if not meeting_id:
                raise ValueError(str(teams_errors.TeamsMeetingIdRequired))
        return meeting_id

    @staticmethod
    def _get_tenant_id(channel_data: ChannelData, tenant_id: str | None = None) -> str:
        if not tenant_id:
            tenant_id = getattr(channel_data.tenant, "id", None)
            if not tenant_id:
                raise ValueError(str(teams_errors.TeamsTenantIdRequired))
        return tenant_id

    @staticmethod
    def _get_team_id(channel_data: ChannelData, team_id: str | None = None) -> str:
        if not team_id:
            team_id = getattr(channel_data.team, "id", None)
            if not team_id:
                raise ValueError(str(teams_errors.TeamsTeamIdRequired))
        return team_id

    @staticmethod
    def _get_conversation_id(context: TurnContext) -> str:
        conversation_id = (
            context.activity.conversation.id if context.activity.conversation else None
        )
        if not conversation_id:
            raise ValueError(str(teams_errors.TeamsConversationIdRequired))
        return conversation_id

    @staticmethod
    async def get_meeting_participant(
        context: TurnContext,
        meeting_id: str | None = None,
        participant_id: str | None = None,
        tenant_id: str | None = None,
    ) -> MeetingParticipant:
        """
        Gets the meeting participant information.

        Args:
            context: The turn context.
            meeting_id: The meeting ID. If not provided, it will be extracted from the activity.
            participant_id: The participant ID. If not provided, it will be extracted from the activity.
            tenant_id: The tenant ID. If not provided, it will be extracted from the activity.

        Returns:
            The meeting participant information.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data: ChannelData = _get_channel_data(context)

        meeting_id = TeamsInfo._get_meeting_id(channel_data, meeting_id)

        if not tenant_id:
            tenant_id = getattr(channel_data.tenant, "id", None)
            if not tenant_id:
                raise ValueError(str(teams_errors.TeamsTenantIdRequired))

        if not participant_id:
            participant_id = getattr(
                context.activity.from_property, "aad_object_id", None
            )
            if not participant_id:
                raise ValueError(str(teams_errors.TeamsParticipantIdRequired))

        api_client = get_cached_teams_api_client(context)
        return await api_client.meetings.get_participant(
            meeting_id, participant_id, tenant_id
        )

    @staticmethod
    async def get_meeting_info(
        context: TurnContext, meeting_id: str | None = None
    ) -> MeetingInfo:
        """
        Gets the meeting information.

        Args:
            context: The turn context.
            meeting_id: The meeting ID. If not provided, it will be extracted from the activity.

        Returns:
            The meeting information.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data: ChannelData = _get_channel_data(context)
        meeting_id = TeamsInfo._get_meeting_id(channel_data, meeting_id)

        api_client = get_cached_teams_api_client(context)
        return await api_client.meetings.get_by_id(meeting_id)

    @staticmethod
    async def get_team_details(
        context: TurnContext, team_id: str | None = None
    ) -> TeamDetails:
        """
        Gets the team details.

        Args:
            context: The turn context.
            team_id: The team ID. If not provided, it will be extracted from the activity.

        Returns:
            The team details.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data: ChannelData = _get_channel_data(context)
        team_id = TeamsInfo._get_team_id(channel_data, team_id)

        api_client = get_cached_teams_api_client(context)
        return await api_client.teams.get_by_id(team_id)

    @staticmethod
    async def get_team_channels(
        context: TurnContext, team_id: str | None = None
    ) -> list[ChannelInfo]:
        """
        Gets the channels of a team.

        Args:
            context: The turn context.
            team_id: The team ID. If not provided, it will be extracted from the activity.

        Returns:
            The list of channels.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data = _get_channel_data(context)
        team_id = TeamsInfo._get_team_id(channel_data, team_id)

        api_client = get_cached_teams_api_client(context)
        return await api_client.teams.get_conversations(team_id)

    @staticmethod
    async def get_paged_members(
        context: TurnContext,
        page_size: int | None = None,
        continuation_token: str = "",
    ) -> PagedMembersResult:
        """
        Gets the paged members of a team or conversation.

        Args:
            context: The turn context.
            page_size: The page size.
            continuation_token: The continuation token.

        Returns:
            The paged members result.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data = _get_channel_data(context)
        team_id = getattr(channel_data.team, "id", None)

        conversation_id = team_id or TeamsInfo._get_conversation_id(context)

        api_client = get_cached_teams_api_client(context)
        return await api_client.conversations.members(conversation_id).get_paged(
            page_size, continuation_token
        )

    @staticmethod
    async def get_member(context: TurnContext, user_id: str) -> TeamsChannelAccount:
        """
        Gets a member of a team or conversation.

        Args:
            context: The turn context.
            user_id: The user ID.

        Returns:
            The member information.

        Raises:
            ValueError: If required parameters are missing.
        """
        channel_data = _get_channel_data(context)
        team_id = getattr(channel_data.team, "id", None)

        if team_id:
            return await TeamsInfo.get_team_member(context, team_id, user_id)
        else:
            conversation_id = TeamsInfo._get_conversation_id(context)

            return await TeamsInfo._get_member_internal(
                context, conversation_id, user_id
            )

    @staticmethod
    async def get_team_member(
        context: TurnContext, team_id: str, user_id: str
    ) -> TeamsChannelAccount:
        """
        Gets a member of a team.

        Args:
            context: The turn context.
            team_id: The team ID.
            user_id: The user ID.

        Returns:
            The member information.

        Raises:
            ValueError: If required parameters are missing.
        """
        api_client = get_cached_teams_api_client(context)
        return await api_client.conversations.members(team_id).get(user_id)

    @staticmethod
    async def _get_member_internal(
        context: TurnContext, conversation_id: str, user_id: str
    ) -> TeamsChannelAccount:
        """
        Internal method to get a member from a conversation.

        Args:
            context: The turn context.
            conversation_id: The conversation ID.
            user_id: The user ID.

        Returns:
            The member information.

        Raises:
            ValueError: If required parameters are missing.
        """
        api_client = get_cached_teams_api_client(context)
        return await api_client.conversations.members(conversation_id).get(user_id)
