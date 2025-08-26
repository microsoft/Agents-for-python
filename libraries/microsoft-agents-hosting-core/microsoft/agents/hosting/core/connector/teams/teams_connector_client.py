# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams Connector Client for Microsoft Agents."""

from typing import Any
from aiohttp import ClientSession

from microsoft.agents.activity import Activity, ResourceResponse
from microsoft.agents.hosting.core.authorization import (
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)
from microsoft.agents.hosting.core.connector.client import ConnectorClient

from microsoft.agents.activity import ConversationParameters
from microsoft.agents.activity.teams import (
    TeamsChannelAccount,
    TeamsPagedMembersResult,
    TeamDetails,
    TeamsMember,
    MeetingInfo,
    MeetingNotification,
    MeetingNotificationResponse,
    TeamsBatchOperationResponse,
    BatchOperationStateResponse,
    BatchFailedEntriesResponse,
    CancelOperationResponse,
    ChannelInfo,
)


class TeamsConnectorClient(ConnectorClient):
    """Teams Connector Client for interacting with Teams-specific APIs."""

    @classmethod
    async def create_client_with_auth_async(
        cls,
        base_url: str,
        auth_config: AgentAuthConfiguration,
        auth_provider: AccessTokenProviderBase,
        scope: str,
    ) -> "TeamsConnectorClient":
        """
        Creates a new instance of TeamsConnectorClient with authentication.

        :param base_url: The base URL for the API.
        :param auth_config: The authentication configuration.
        :param auth_provider: The authentication provider.
        :param scope: The scope for the authentication token.
        :return: A new instance of TeamsConnectorClient.
        """
        session = ClientSession(
            base_url=base_url, headers={"Accept": "application/json"}
        )

        token = await auth_provider.get_access_token(auth_config, scope)
        if len(token) > 1:
            session.headers.update({"Authorization": f"Bearer {token}"})

        return cls(session)

    async def get_conversation_member(
        self, conversation_id: str, user_id: str
    ) -> TeamsChannelAccount:
        """
        Get a member from a conversation.

        :param conversation_id: The ID of the conversation to get the member from.
        :param user_id: The ID of the user to get.
        :return: The Teams channel account for the user.
        """
        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not user_id:
            raise ValueError("user_id is required")

        async with self.client.get(
            f"v3/conversations/{conversation_id}/members/{user_id}",
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()

            json_response = await response.json()
            return TeamsChannelAccount.model_validate(json_response)

    async def get_conversation_paged_member(
        self, conversation_id: str, page_size: int, continuation_token: str
    ) -> TeamsPagedMembersResult:
        """
        Get paged members from a conversation.

        :param conversation_id: The ID of the conversation to get the members from.
        :param page_size: The number of members to return per page.
        :param continuation_token: The continuation token for paging.
        :return: The paged members result.
        """
        async with self.client.get(
            f"v3/conversations/{conversation_id}/pagedMembers",
            params={
                "pageSize": page_size,
                "continuationToken": continuation_token or "",
            },
        ) as response:
            response.raise_for_status()
            return TeamsPagedMembersResult.model_validate(await response.json())

    async def fetch_channel_list(self, team_id: str) -> list[ChannelInfo]:
        """
        Fetch the list of channels in a team.

        :param team_id: The ID of the team to fetch channels from.
        :return: The list of channels.
        """
        async with self.client.get(f"v3/teams/{team_id}/conversations") as response:
            response.raise_for_status()
            json_response = await response.json()
            channels_data = json_response.get("conversations", [])
            return [ChannelInfo.model_validate(channel) for channel in channels_data]

    async def fetch_team_details(self, team_id: str) -> TeamDetails:
        """
        Fetch the details of a team.

        :param team_id: The ID of the team to fetch details for.
        :return: The team details.
        """
        async with self.client.get(f"v3/teams/{team_id}") as response:
            response.raise_for_status()
            return TeamDetails.model_validate(await response.json())

    async def fetch_meeting_participant(
        self, meeting_id: str, participant_id: str, tenant_id: str
    ) -> Any:
        """
        Fetch a participant from a meeting.

        :param meeting_id: The ID of the meeting to fetch the participant from.
        :param participant_id: The ID of the participant to fetch.
        :param tenant_id: The ID of the tenant.
        :return: The participant information.
        """
        async with self.client.get(
            f"v1/meetings/{meeting_id}/participants/{participant_id}",
            params={"tenantId": tenant_id},
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def fetch_meeting_info(self, meeting_id: str) -> MeetingInfo:
        """
        Fetch information about a meeting.

        :param meeting_id: The ID of the meeting to fetch information for.
        :return: The meeting information.
        """
        async with self.client.get(f"v1/meetings/{meeting_id}") as response:
            response.raise_for_status()
            return MeetingInfo.model_validate(await response.json())

    async def create_conversation(
        self, conversation_parameters: ConversationParameters
    ) -> ResourceResponse:
        """
        Creates a new conversation.

        :param conversation_parameters: Parameters to create the conversation.
        :return: A resource response with the conversation ID.
        """
        async with self.client.post(
            "v3/conversations",
            json=conversation_parameters.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            return ResourceResponse.model_validate(await response.json())

    async def send_meeting_notification(
        self, meeting_id: str, notification: MeetingNotification
    ) -> MeetingNotificationResponse:
        """
        Send a notification to a meeting.

        :param meeting_id: The ID of the meeting to send the notification to.
        :param notification: The notification to send.
        :return: The notification response.
        """
        async with self.client.post(
            f"v1/meetings/{meeting_id}/notification",
            json=notification.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
        ) as response:
            response.raise_for_status()
            return MeetingNotificationResponse.model_validate(await response.json())

    async def send_message_to_list_of_users(
        self, activity: Activity, tenant_id: str, members: list[TeamsMember]
    ) -> TeamsBatchOperationResponse:
        """
        Send a message to a list of users.

        :param activity: The activity to send.
        :param tenant_id: The ID of the tenant.
        :param members: The list of members to send to.
        :return: The batch operation response.
        """
        content = {
            "activity": activity.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
            "members": [
                member.model_dump(by_alias=True, exclude_unset=True, mode="json")
                for member in members
            ],
            "tenantId": tenant_id,
        }

        async with self.client.post(
            "v3/batch/conversation/users", json=content
        ) as response:
            response.raise_for_status()
            return TeamsBatchOperationResponse.model_validate(await response.json())

    async def send_message_to_all_users_in_tenant(
        self, activity: Activity, tenant_id: str
    ) -> TeamsBatchOperationResponse:
        """
        Send a message to all users in a tenant.

        :param activity: The activity to send.
        :param tenant_id: The ID of the tenant.
        :return: The batch operation response.
        """
        content = {
            "activity": activity.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
            "tenantId": tenant_id,
        }

        async with self.client.post(
            "v3/batch/conversation/tenant", json=content
        ) as response:
            response.raise_for_status()
            return TeamsBatchOperationResponse.model_validate(await response.json())

    async def send_message_to_all_users_in_team(
        self, activity: Activity, tenant_id: str, team_id: str
    ) -> TeamsBatchOperationResponse:
        """
        Send a message to all users in a team.

        :param activity: The activity to send.
        :param tenant_id: The ID of the tenant.
        :param team_id: The ID of the team.
        :return: The batch operation response.
        """
        content = {
            "activity": activity.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
            "tenantId": tenant_id,
            "teamId": team_id,
        }

        async with self.client.post(
            "v3/batch/conversation/team", json=content
        ) as response:
            response.raise_for_status()
            return TeamsBatchOperationResponse.model_validate(await response.json())

    async def send_message_to_list_of_channels(
        self, activity: Activity, tenant_id: str, members: list[TeamsMember]
    ) -> TeamsBatchOperationResponse:
        """
        Send a message to a list of channels.

        :param activity: The activity to send.
        :param tenant_id: The ID of the tenant.
        :param members: The list of members to send to.
        :return: The batch operation response.
        """
        content = {
            "activity": activity.model_dump(
                by_alias=True, exclude_unset=True, mode="json"
            ),
            "tenantId": tenant_id,
            "members": [
                member.model_dump(by_alias=True, exclude_unset=True, mode="json")
                for member in members
            ],
        }

        async with self.client.post(
            "v3/batch/conversation/channels", json=content
        ) as response:
            response.raise_for_status()
            return TeamsBatchOperationResponse.model_validate(await response.json())

    async def get_operation_state(
        self, operation_id: str
    ) -> BatchOperationStateResponse:
        """
        Get the state of a batch operation.

        :param operation_id: The ID of the operation to get the state for.
        :return: The operation state.
        """
        async with self.client.get(f"v3/batch/conversation/{operation_id}") as response:
            response.raise_for_status()
            return BatchOperationStateResponse.model_validate(await response.json())

    async def get_failed_entries(self, operation_id: str) -> BatchFailedEntriesResponse:
        """
        Get failed entries from a batch operation.

        :param operation_id: The ID of the operation to get failed entries for.
        :return: The failed entries.
        """
        async with self.client.get(
            f"v3/batch/conversation/failedentries/{operation_id}"
        ) as response:
            response.raise_for_status()
            return BatchFailedEntriesResponse.model_validate(await response.json())

    async def cancel_operation(self, operation_id: str) -> CancelOperationResponse:
        """
        Cancel a batch operation.

        :param operation_id: The ID of the operation to cancel.
        :return: The cancel operation response.
        """
        async with self.client.delete(
            f"v3/batch/conversation/{operation_id}"
        ) as response:
            response.raise_for_status()
            return CancelOperationResponse.model_validate(await response.json())

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.client:
            await self.client.close()
