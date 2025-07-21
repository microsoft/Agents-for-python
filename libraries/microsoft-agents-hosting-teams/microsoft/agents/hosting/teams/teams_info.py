# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams information utilities for Microsoft Agents."""

from typing import Optional, Tuple, Dict, Any, List

from microsoft.agents.activity import Activity, Channels, ConversationParameters

from microsoft.agents.activity.teams import (
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
from microsoft.agents.hosting.core.connector.teams import TeamsConnectorClient
from microsoft.agents.hosting.core import ChannelServiceAdapter, TurnContext


class TeamsInfo:
    """Teams information utilities for interacting with Teams-specific data."""

    @staticmethod
    async def get_meeting_participant(
        context: TurnContext,
        meeting_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> TeamsMeetingParticipant:
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
        if not context:
            raise ValueError("context is required.")

        activity = context.activity
        teams_channel_data: dict = activity.channel_data

        if meeting_id is None:
            meeting_id = teams_channel_data.get("meeting", {}).get("id", None)

        if not meeting_id:
            raise ValueError("meeting_id is required.")

        if participant_id is None:
            participant_id = getattr(activity.from_property, "aad_object_id", None)

        if not participant_id:
            raise ValueError("participant_id is required.")

        if tenant_id is None:
            tenant_id = teams_channel_data.get("tenant", {}).get("id", None)

        rest_client = TeamsInfo._get_rest_client(context)
        result = await rest_client.fetch_meeting_participant(
            meeting_id, participant_id, tenant_id
        )
        return result

    @staticmethod
    async def get_meeting_info(
        context: TurnContext, meeting_id: Optional[str] = None
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
        if not meeting_id:
            teams_channel_data: dict = context.activity.channel_data
            meeting_id = teams_channel_data.get("meeting", {}).get("id", None)

        if not meeting_id:
            raise ValueError("meeting_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        result = await rest_client.fetch_meeting_info(meeting_id)
        return result

    @staticmethod
    async def get_team_details(
        context: TurnContext, team_id: Optional[str] = None
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
        if not team_id:
            teams_channel_data: dict = context.activity.channel_data
            team_id = teams_channel_data.get("team", {}).get("id", None)

        if not team_id:
            raise ValueError("team_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        result = await rest_client.fetch_team_details(team_id)
        return result

    @staticmethod
    async def send_message_to_teams_channel(
        context: TurnContext,
        activity: Activity,
        teams_channel_id: str,
        app_id: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Sends a message to a Teams channel.

        Args:
            context: The turn context.
            activity: The activity to send.
            teams_channel_id: The Teams channel ID.
            app_id: The application ID.

        Returns:
            A tuple containing the conversation reference and new activity ID.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not context:
            raise ValueError("TurnContext cannot be None")

        if not activity:
            raise ValueError("Activity cannot be None")

        if not teams_channel_id:
            raise ValueError("The teams_channel_id cannot be None or empty")

        convo_params = ConversationParameters(
            is_group=True,
            channel_data={
                "channel": {
                    "id": teams_channel_id,
                },
            },
            activity=activity,
            agent=context.activity.recipient,
        )

        conversation_reference = None
        new_activity_id = None

        if app_id and isinstance(context.adapter, ChannelServiceAdapter):

            async def _conversation_callback(
                turn_context: TurnContext,
            ) -> None:
                """
                Callback for create_conversation.

                Args:
                    turn_context: The turn context.
                    conversation_reference: The conversation reference to update.
                    new_activity_id: The new activity ID to update.
                """
                nonlocal conversation_reference, new_activity_id
                conversation_reference = (
                    turn_context.activity.get_conversation_reference()
                )
                new_activity_id = turn_context.activity.id

            await context.adapter.create_conversation(
                app_id,
                Channels.ms_teams,
                context.activity.service_url,
                "https://api.botframework.com",
                convo_params,
                _conversation_callback,
            )
        else:
            connector_client = TeamsInfo._get_rest_client(context)
            conversation_resource_response = (
                await connector_client.conversations.create_conversation(convo_params)
            )
            conversation_reference = context.activity.get_conversation_reference()
            conversation_reference.conversation.id = conversation_resource_response.id
            new_activity_id = conversation_resource_response.activity_id

        return conversation_reference, new_activity_id

    @staticmethod
    async def get_team_channels(
        context: TurnContext, team_id: Optional[str] = None
    ) -> List[ChannelInfo]:
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
        if not team_id:
            teams_channel_data: dict = context.activity.channel_data
            team_id = teams_channel_data.get("team", {}).get("id", None)

        if not team_id:
            raise ValueError("team_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.fetch_channel_list(team_id)

    @staticmethod
    async def get_paged_members(
        context: TurnContext,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> TeamsPagedMembersResult:
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
        teams_channel_data: dict = context.activity.channel_data
        team_id = teams_channel_data.get("team", {}).get("id", None)

        if team_id:
            return await TeamsInfo.get_paged_team_members(
                context, team_id, page_size, continuation_token
            )
        else:
            conversation_id = (
                context.activity.conversation.id
                if context.activity.conversation
                else None
            )
            if not conversation_id:
                raise ValueError("conversation_id is required.")

            rest_client = TeamsInfo._get_rest_client(context)
            return await rest_client.get_conversation_paged_member(
                conversation_id, page_size, continuation_token
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
        teams_channel_data: dict = context.activity.channel_data
        team_id = teams_channel_data.get("team", {}).get("id", None)

        if team_id:
            return await TeamsInfo.get_team_member(context, team_id, user_id)
        else:
            conversation_id = (
                context.activity.conversation.id
                if context.activity.conversation
                else None
            )
            if not conversation_id:
                raise ValueError("conversation_id is required.")

            return await TeamsInfo._get_member_internal(
                context, conversation_id, user_id
            )

    @staticmethod
    async def get_paged_team_members(
        context: TurnContext,
        team_id: Optional[str] = None,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> TeamsPagedMembersResult:
        """
        Gets the paged members of a team.

        Args:
            context: The turn context.
            team_id: The team ID. If not provided, it will be extracted from the activity.
            page_size: The page size.
            continuation_token: The continuation token.

        Returns:
            The paged members result.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not team_id:
            teams_channel_data: dict = context.activity.channel_data
            team_id = teams_channel_data.get("team", {}).get("id", None)

        if not team_id:
            raise ValueError("team_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        paged_results = await rest_client.get_conversation_paged_member(
            team_id, page_size, continuation_token
        )

        # Fetch all pages if there are more
        while paged_results.continuation_token:
            next_results = await rest_client.get_conversation_paged_member(
                team_id, page_size, paged_results.continuation_token
            )
            paged_results.members.extend(next_results.members)
            paged_results.continuation_token = next_results.continuation_token

        return paged_results

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
        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.get_conversation_member(team_id, user_id)

    @staticmethod
    async def send_meeting_notification(
        context: TurnContext,
        notification: MeetingNotification,
        meeting_id: Optional[str] = None,
    ) -> MeetingNotificationResponse:
        """
        Sends a meeting notification.

        Args:
            context: The turn context.
            notification: The meeting notification.
            meeting_id: The meeting ID. If not provided, it will be extracted from the activity.

        Returns:
            The meeting notification response.

        Raises:
            ValueError: If required parameters are missing.
        """
        activity = context.activity

        if meeting_id is None:
            teams_channel_data: dict = activity.channel_data
            meeting_id = teams_channel_data.get("meeting", {}).get("id", None)

        if not meeting_id:
            raise ValueError("meeting_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.send_meeting_notification(meeting_id, notification)

    @staticmethod
    async def send_message_to_list_of_users(
        context: TurnContext,
        activity: Activity,
        tenant_id: str,
        members: List[TeamsMember],
    ) -> TeamsBatchOperationResponse:
        """
        Sends a message to a list of users.

        Args:
            context: The turn context.
            activity: The activity to send.
            tenant_id: The tenant ID.
            members: The list of members.

        Returns:
            The batch operation response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not activity:
            raise ValueError("activity is required.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")
        if not members or len(members) == 0:
            raise ValueError("members list is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.send_message_to_list_of_users(
            activity, tenant_id, members
        )

    @staticmethod
    async def send_message_to_all_users_in_tenant(
        context: TurnContext, activity: Activity, tenant_id: str
    ) -> TeamsBatchOperationResponse:
        """
        Sends a message to all users in a tenant.

        Args:
            context: The turn context.
            activity: The activity to send.
            tenant_id: The tenant ID.

        Returns:
            The batch operation response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not activity:
            raise ValueError("activity is required.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.send_message_to_all_users_in_tenant(
            activity, tenant_id
        )

    @staticmethod
    async def send_message_to_all_users_in_team(
        context: TurnContext, activity: Activity, tenant_id: str, team_id: str
    ) -> TeamsBatchOperationResponse:
        """
        Sends a message to all users in a team.

        Args:
            context: The turn context.
            activity: The activity to send.
            tenant_id: The tenant ID.
            team_id: The team ID.

        Returns:
            The batch operation response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not activity:
            raise ValueError("activity is required.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")
        if not team_id:
            raise ValueError("team_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.send_message_to_all_users_in_team(
            activity, tenant_id, team_id
        )

    @staticmethod
    async def send_message_to_list_of_channels(
        context: TurnContext,
        activity: Activity,
        tenant_id: str,
        members: List[TeamsMember],
    ) -> TeamsBatchOperationResponse:
        """
        Sends a message to a list of channels.

        Args:
            context: The turn context.
            activity: The activity to send.
            tenant_id: The tenant ID.
            members: The list of members.

        Returns:
            The batch operation response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not activity:
            raise ValueError("activity is required.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")
        if not members or len(members) == 0:
            raise ValueError("members list is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.send_message_to_list_of_channels(
            activity, tenant_id, members
        )

    @staticmethod
    async def get_operation_state(
        context: TurnContext, operation_id: str
    ) -> BatchOperationStateResponse:
        """
        Gets the operation state.

        Args:
            context: The turn context.
            operation_id: The operation ID.

        Returns:
            The operation state response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not operation_id:
            raise ValueError("operation_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.get_operation_state(operation_id)

    @staticmethod
    async def get_failed_entries(
        context: TurnContext, operation_id: str
    ) -> BatchFailedEntriesResponse:
        """
        Gets the failed entries of an operation.

        Args:
            context: The turn context.
            operation_id: The operation ID.

        Returns:
            The failed entries response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not operation_id:
            raise ValueError("operation_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.get_failed_entries(operation_id)

    @staticmethod
    async def cancel_operation(
        context: TurnContext, operation_id: str
    ) -> CancelOperationResponse:
        """
        Cancels an operation.

        Args:
            context: The turn context.
            operation_id: The operation ID.

        Returns:
            The cancel operation response.

        Raises:
            ValueError: If required parameters are missing.
        """
        if not operation_id:
            raise ValueError("operation_id is required.")

        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.cancel_operation(operation_id)

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
        rest_client = TeamsInfo._get_rest_client(context)
        return await rest_client.get_conversation_member(conversation_id, user_id)

    @staticmethod
    def _get_rest_client(context: TurnContext) -> TeamsConnectorClient:
        """
        Gets the Teams connector client from the context.

        Args:
            context: The turn context.

        Returns:
            The Teams connector client.

        Raises:
            ValueError: If the client is not available in the context.
        """
        # TODO: Varify key
        client = context.turn_state.get("ConnectorClient")
        if not client:
            raise ValueError("TeamsConnectorClient is not available in the context.")
        return client
