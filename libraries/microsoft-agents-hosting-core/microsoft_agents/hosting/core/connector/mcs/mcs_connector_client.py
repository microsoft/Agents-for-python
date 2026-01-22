# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""MCS Connector Client for Microsoft Copilot Studio via Power Apps Connector."""

import logging
from typing import Optional
from aiohttp import ClientSession

from microsoft_agents.activity import Activity, ResourceResponse
from ..connector_client_base import ConnectorClientBase
from ..attachments_base import AttachmentsBase
from ..conversations_base import ConversationsBase

logger = logging.getLogger(__name__)


class MCSConversations(ConversationsBase):
    """
    Conversations implementation for Microsoft Copilot Studio Connector.

    Only supports SendToConversation and ReplyToActivity operations.
    """

    def __init__(self, client: ClientSession, endpoint: str):
        self._client = client
        self._endpoint = endpoint

    async def send_to_conversation(
        self,
        conversation_id: str,
        activity: Activity,
        **kwargs,
    ) -> ResourceResponse:
        """
        Send an activity to a conversation.

        :param conversation_id: The conversation ID (not used for MCS connector).
        :param activity: The activity to send.
        :return: A resource response.
        """
        if activity is None:
            raise ValueError("activity is required")

        logger.info(
            "MCS Connector: Sending activity to conversation: %s. Activity type is %s",
            conversation_id,
            activity.type,
        )

        async with self._client.post(
            self._endpoint,
            json=activity.model_dump(by_alias=True, exclude_unset=True, mode="json"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        ) as response:
            if response.status >= 300:
                logger.error(
                    "MCS Connector: Error sending activity: %s", response.status
                )
                response.raise_for_status()

            # Check if there's a response body
            content = await response.text()
            if content:
                data = await response.json()
                # TODO: (connector) Validate response structure
                return ResourceResponse(**data)

            return ResourceResponse(id="")

    async def reply_to_activity(
        self,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
        **kwargs,
    ) -> ResourceResponse:
        """
        Reply to an activity in a conversation.

        For MCS Connector, this falls back to send_to_conversation.

        :param conversation_id: The conversation ID.
        :param activity_id: The activity ID to reply to.
        :param activity: The activity to send.
        :return: A resource response.
        """
        return await self.send_to_conversation(conversation_id, activity, **kwargs)

    async def update_activity(
        self,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
        **kwargs,
    ) -> ResourceResponse:
        """Not supported for MCS Connector."""
        raise RuntimeError(
            "UpdateActivity is not supported for Microsoft Copilot Studio Connector"
        )

    async def delete_activity(
        self, conversation_id: str, activity_id: str, **kwargs
    ) -> None:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "DeleteActivity is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_conversation_member(self, conversation_id: str, **kwargs) -> list:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetConversationMembers is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_conversation_members(self, conversation_id: str, **kwargs) -> list:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetConversationMembers is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_activity_members(
        self, conversation_id: str, activity_id: str, **kwargs
    ) -> list:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetActivityMembers is not supported for Microsoft Copilot Studio Connector"
        )

    async def delete_conversation_member(
        self, conversation_id: str, member_id: str, **kwargs
    ) -> None:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "DeleteConversationMember is not supported for Microsoft Copilot Studio Connector"
        )

    async def send_conversation_history(
        self, conversation_id: str, transcript: dict, **kwargs
    ) -> ResourceResponse:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "SendConversationHistory is not supported for Microsoft Copilot Studio Connector"
        )

    async def upload_attachment(
        self, conversation_id: str, attachment_upload: dict, **kwargs
    ) -> ResourceResponse:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "UploadAttachment is not supported for Microsoft Copilot Studio Connector"
        )

    async def create_conversation(self, parameters: dict, **kwargs) -> dict:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "CreateConversation is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_conversations(
        self, continuation_token: Optional[str] = None, **kwargs
    ) -> dict:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetConversations is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_conversation_paged_members(
        self,
        conversation_id: str,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetConversationPagedMembers is not supported for Microsoft Copilot Studio Connector"
        )


class MCSAttachments(AttachmentsBase):
    """
    Attachments implementation for Microsoft Copilot Studio Connector.

    Attachments operations are not supported.
    """

    async def get_attachment_info(self, attachment_id: str, **kwargs) -> dict:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetAttachmentInfo is not supported for Microsoft Copilot Studio Connector"
        )

    async def get_attachment(self, attachment_id: str, view_id: str, **kwargs) -> bytes:
        """Not supported for MCS Connector."""
        raise NotImplementedError(
            "GetAttachment is not supported for Microsoft Copilot Studio Connector"
        )


class MCSConnectorClient(ConnectorClientBase):
    """
    Connector client suited for communicating with Microsoft Copilot Studio
    via a Power Apps Connector request.

    Only supports SendToConversation and ReplyToActivity operations.
    All other operations will raise NotImplementedError.
    """

    def __init__(self, endpoint: str, client: Optional[ClientSession] = None):
        """
        Initialize the MCS Connector Client.

        :param endpoint: The endpoint URL for the MCS connector.
        :param client: Optional aiohttp ClientSession. If not provided, one will be created.
        """
        if not endpoint:
            raise ValueError("endpoint is required")

        self._endpoint = endpoint
        self._client = client or ClientSession()
        self._conversations = MCSConversations(self._client, self._endpoint)
        self._attachments = MCSAttachments()

    @property
    def base_uri(self) -> str:
        """Get the base URI for this connector client."""
        return self._endpoint

    @property
    def attachments(self) -> AttachmentsBase:
        """Get the attachments operations (not supported for MCS)."""
        return self._attachments

    @property
    def conversations(self) -> ConversationsBase:
        """Get the conversations operations."""
        return self._conversations

    async def close(self):
        """Close the client session."""
        if self._client:
            await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
