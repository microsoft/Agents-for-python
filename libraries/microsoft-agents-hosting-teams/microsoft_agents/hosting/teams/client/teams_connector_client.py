from pydantic import BaseModel

from .models import (
    TeamDetails,
    TeamsMember,
    TeamsPagedMembersResult,
    BatchFailedEntriesResponse,
    BatchFailedEntry,
    BatchOperationsStateResponse,
    CancelOperationResponse,
    ResourceResponse,
    TeamsBatchOperationResponse,
)
from microsoft_agents.activity import Activity, ChannelAccount
from microsoft_agents.hosting.core import ConnectorClient


class ConversationList(BaseModel):
    conversations: list[ChannelInfo] = []


class TeamsConnectorClient:
    def __init__(self, connector_client: ConnectorClient):
        self._connector_client = connector_client

    @classmethod
    async def get_member(cls, activity: Activity, user_id: str) -> TeamsChannelAccount:
        teams_channel_data = activity.channel_data
        team_id = teams_channel_data.team.id
        if team_id:
            return await cls.get_team_member(activity, team_id, user_id)
        else:
            if activity.conversation and activity.conversation.id:
                conversation_id = activity.conversation.id
            else:
                conversation_id = None
            return await cls.get_member_internal(activity, conversation_id, user_id)

    @staticmethod
    async def get_team_id(activity: Activity) -> str:
        channel_data = activity.channel_data
        team = channel_data.team if channel_data else None
        return team.id if team else None  # robrandao: TODO compare with JS

    @classmethod
    async def get_team_member(
        cls, activity: Activity, team_id: str, user_id: str
    ) -> TeamsChannelAccount:
        return await cls.get_member_internal(activity, team_id, user_id, is_team=True)

    async def get_conversation_member(
        self, conversation_id: str, user_id: str
    ) -> ChannelAccount:
        # robrandao: TODO -> request
        pass

    @classmethod
    async def get_member_internal(
        cls, activity: Activity, conversation_id: str, user_id: str
    ):
        # robrandao -> Excuse me, why.
        client = activity.turn_state.get(activity.adapter.connector_client_key)
        if not client:
            raise Exception("Client is not available in the context.")
        team_member = await client.get_conversation_member(conversation_id, user_id)
        return team_member

    async def get_conversation_paged_member(
        self, conversation_id: str, page_size: int, continuation_token: str
    ) -> TeamsPagedMembersResult:
        # robrandao: TODO -> request
        pass

    async def fetch_channel_list(self, team_id: str) -> list[ChannelInfo]:
        # robrandao: TODO -> request
        pass

    async def fetch_team_details(self, team_id: str) -> TeamDetails:
        # robrandao: TODO -> request
        pass

    async def fetch_meeting_participant(
        self, meeting_id: str, participant_id: str, tenant_id: str
    ) -> str:
        pass  # robrandao: TODO -> request

    async def fetch_meeting_info(self, meeting_id: str) -> MeetingInfo:
        pass  # robrandao: TODO -> request

    async def send_meeting_notification(
        self, meeting_id: str, notification: MeetingNotification
    ) -> MeetingNotificationResponse:
        pass  # robrandao: TODO -> request

    async def send_message_to_list_of_users(
        self, activity: Activity, tenant_id: str, members: list[TeamsMember]
    ) -> TeamsBatchOperationResponse:
        pass  # robrandao: TODO -> request

    async def send_message_to_all_users_in_tenant(
        self, activity: Activity, tenant_id: str
    ) -> TeamsBatchOperationResponse:
        pass  # robrandao: TODO -> request

    async def send_message_to_all_users_in_team(
        self, activity: Activity, tenant_id: str, team_id: str
    ) -> TeamsBatchOperationResponse:
        pass  # robrandao: TODO -> request

    async def send_message_to_list_of_channels(
        self, activity: Activity, tenant_id: str, members: list[TeamsMember]
    ) -> TeamsBatchOperationResponse:
        pass  # robrandao: TODO -> request

    async def get_operation_state(
        self, operation_id: str
    ) -> BatchOperationStateResponse:
        pass  # robrandao: TODO -> request

    async def get_failed_entries(self, operation_id: str) -> BatchFailedEntriesResponse:
        pass  # robrandao: TODO -> request

    async def cancel_operation(self, operation_id: str) -> CancelOperationResponse:
        pass  # robrandao: TODO -> request
