# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Connector Client for Microsoft Agents."""

import logging
from typing import Any, Optional
import json
from aiohttp import ClientSession
from io import BytesIO

from microsoft.agents.core.models import (
    Activity,
    ChannelAccount,
    ConversationParameters,
    ConversationResourceResponse,
    ResourceResponse,
    ConversationsResult,
    PagedMembersResult,
)
from microsoft.agents.authorization import (
    AccessTokenProviderBase,
)
from microsoft.agents.connector import ConnectorClientBase
from ..attachments_base import AttachmentsBase
from ..conversations_base import ConversationsBase


logger = logging.getLogger("microsoft.agents.connector.client")


class AttachmentInfo:
    """Information about an attachment."""

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.type = kwargs.get("type")
        self.views = kwargs.get("views")


class AttachmentData:
    """Data for an attachment."""

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.original_base64 = kwargs.get("originalBase64")
        self.type = kwargs.get("type")
        self.thumbnail_base64 = kwargs.get("thumbnailBase64")


def normalize_outgoing_activity(data: Any) -> Any:
    """
    Normalizes an outgoing activity object for wire transmission.

    :param data: The activity object to normalize.
    :return: The normalized activity object.
    """
    # This is a placeholder for any transformations needed
    # Similar to the normalizeOutgoingActivity function in TypeScript
    return data


class AttachmentsOperations(AttachmentsBase):

    def __init__(self, client: ClientSession):
        self.client = client

    async def get_attachment_info(self, attachment_id: str) -> AttachmentInfo:
        """
        Retrieves attachment information by attachment ID.

        :param attachment_id: The ID of the attachment.
        :return: The attachment information.
        """
        if attachment_id is None:
            raise ValueError("attachmentId is required")

        url = f"v3/attachments/{attachment_id}"

        async with self.client.get(url) as response:
            if response.status >= 400:
                logger.error(f"Error getting attachment info: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return AttachmentInfo(**data)

    async def get_attachment(self, attachment_id: str, view_id: str) -> BytesIO:
        """
        Retrieves an attachment by attachment ID and view ID.

        :param attachment_id: The ID of the attachment.
        :param view_id: The ID of the view.
        :return: The attachment as a readable stream.
        """
        if attachment_id is None:
            raise ValueError("attachmentId is required")
        if view_id is None:
            raise ValueError("viewId is required")

        url = f"v3/attachments/{attachment_id}/views/{view_id}"

        async with self.client.get(url) as response:
            if response.status >= 400:
                logger.error(f"Error getting attachment: {response.status}")
                response.raise_for_status()

            data = await response.read()
            return BytesIO(data)


class ConversationsOperations(ConversationsBase):

    def __init__(self, client: ClientSession):
        self.client = client

    async def get_conversations(
        self, continuation_token: Optional[str] = None
    ) -> ConversationsResult:
        """
        Retrieves a list of conversations.

        :param continuation_token: The continuation token for pagination.
        :return: A list of conversations.
        """
        params = (
            {"continuationToken": continuation_token} if continuation_token else None
        )

        async with self.client.get("v3/conversations", params=params) as response:
            if response.status >= 400:
                logger.error(f"Error getting conversations: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ConversationsResult.model_validate(data)

    async def create_conversation(
        self, body: ConversationParameters
    ) -> ConversationResourceResponse:
        """
        Creates a new conversation.

        :param body: The conversation parameters.
        :return: The conversation resource response.
        """

        async with self.client.post(
            "v3/conversations",
            json=body.model_dump(by_alias=True, exclude_unset=True),
        ) as response:
            if response.status >= 400:
                logger.error(f"Error creating conversation: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ConversationResourceResponse.model_validate(data)

    async def reply_to_activity(
        self, conversation_id: str, activity_id: str, body: Activity
    ) -> ResourceResponse:
        """
        Replies to an activity in a conversation.

        :param conversation_id: The ID of the conversation.
        :param activity_id: The ID of the activity.
        :param body: The activity object.
        :return: The resource response.
        """
        if not conversation_id or not activity_id:
            raise ValueError("conversationId and activityId are required")

        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        async with self.client.post(
            url,
            json=body.model_dump(by_alias=True, exclude_unset=True),
        ) as response:
            if response.status >= 400:
                logger.error(f"Error replying to activity: {response.status}")
                response.raise_for_status()

            data = await response.json() if response.content_length else {}
            logger.info(
                f"Reply to conversation/activity: {data.get('id')}, {activity_id}"
            )
            return ResourceResponse.model_validate(data)

    async def send_to_conversation(
        self, conversation_id: str, body: Activity
    ) -> ResourceResponse:
        """
        Sends an activity to a conversation.

        :param conversation_id: The ID of the conversation.
        :param body: The activity object.
        :return: The resource response.
        """
        if not conversation_id:
            raise ValueError("conversationId is required")

        url = f"v3/conversations/{conversation_id}/activities"

        async with self.client.post(
            url,
            json=body.model_dump(by_alias=True, exclude_unset=True),
        ) as response:
            if response.status >= 400:
                logger.error(f"Error sending to conversation: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ResourceResponse.model_validate(data)

    async def update_activity(
        self, conversation_id: str, activity_id: str, body: Activity
    ) -> ResourceResponse:
        """
        Updates an activity in a conversation.

        :param conversation_id: The ID of the conversation.
        :param activity_id: The ID of the activity.
        :param body: The activity object.
        :return: The resource response.
        """
        if not conversation_id or not activity_id:
            raise ValueError("conversationId and activityId are required")

        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        async with self.client.put(
            url,
            json=body.model_dump(by_alias=True, exclude_unset=True),
        ) as response:
            if response.status >= 400:
                logger.error(f"Error updating activity: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ResourceResponse.model_validate(data)

    async def delete_activity(self, conversation_id: str, activity_id: str) -> None:
        """
        Deletes an activity from a conversation.

        :param conversation_id: The ID of the conversation.
        :param activity_id: The ID of the activity.
        """
        if not conversation_id or not activity_id:
            raise ValueError("conversationId and activityId are required")

        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        async with self.client.delete(url) as response:
            if response.status >= 400:
                logger.error(f"Error deleting activity: {response.status}")
                response.raise_for_status()

    async def upload_attachment(
        self, conversation_id: str, body: AttachmentData
    ) -> ResourceResponse:
        """
        Uploads an attachment to a conversation.

        :param conversation_id: The ID of the conversation.
        :param body: The attachment data.
        :return: The resource response.
        """
        if conversation_id is None:
            raise ValueError("conversationId is required")

        url = f"v3/conversations/{conversation_id}/attachments"

        # Convert the AttachmentData to a dictionary
        attachment_dict = {
            "name": body.name,
            "originalBase64": body.original_base64,
            "type": body.type,
            "thumbnailBase64": body.thumbnail_base64,
        }

        async with self.client.post(url, json=attachment_dict) as response:
            if response.status >= 400:
                logger.error(f"Error uploading attachment: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ResourceResponse.model_validate(data)

    async def get_conversation_members(
        self, conversation_id: str
    ) -> list[ChannelAccount]:
        """
        Gets the members of a conversation.

        :param conversation_id: The ID of the conversation.
        :return: A list of members.
        """
        if not conversation_id:
            raise ValueError("conversationId is required")

        url = f"v3/conversations/{conversation_id}/members"

        async with self.client.get(url) as response:
            if response.status >= 400:
                logger.error(f"Error getting conversation members: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return [ChannelAccount.model_validate(member) for member in data]

    async def get_conversation_member(
        self, conversation_id: str, member_id: str
    ) -> ChannelAccount:
        """
        Gets a member of a conversation.

        :param conversation_id: The ID of the conversation.
        :param member_id: The ID of the member.
        :return: The member.
        """
        if not conversation_id or not member_id:
            raise ValueError("conversationId and memberId are required")

        url = f"v3/conversations/{conversation_id}/members/{member_id}"

        async with self.client.get(url) as response:
            if response.status >= 400:
                logger.error(f"Error getting conversation member: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ChannelAccount.model_validate(data)

    async def delete_conversation_member(
        self, conversation_id: str, member_id: str
    ) -> None:
        """
        Deletes a member from a conversation.

        :param conversation_id: The ID of the conversation.
        :param member_id: The ID of the member.
        """
        if not conversation_id or not member_id:
            raise ValueError("conversationId and memberId are required")

        url = f"v3/conversations/{conversation_id}/members/{member_id}"

        async with self.client.delete(url) as response:
            if response.status >= 400 and response.status != 204:
                logger.error(f"Error deleting conversation member: {response.status}")
                response.raise_for_status()

    async def get_activity_members(
        self, conversation_id: str, activity_id: str
    ) -> list[ChannelAccount]:
        """
        Gets the members who were involved in an activity.

        :param conversation_id: The ID of the conversation.
        :param activity_id: The ID of the activity.
        :return: A list of members.
        """
        if not conversation_id or not activity_id:
            raise ValueError("conversationId and activityId are required")

        url = f"v3/conversations/{conversation_id}/activities/{activity_id}/members"

        async with self.client.get(url) as response:
            if response.status >= 400:
                logger.error(f"Error getting activity members: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return [ChannelAccount.model_validate(member) for member in data]

    async def get_conversation_paged_members(
        self,
        conversation_id: str,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> PagedMembersResult:
        """
        Gets the members of a conversation with pagination.

        :param conversation_id: The ID of the conversation.
        :param page_size: The page size.
        :param continuation_token: The continuation token for pagination.
        :return: A paged list of members.
        """
        if not conversation_id:
            raise ValueError("conversationId is required")

        params = {}
        if page_size is not None:
            params["pageSize"] = str(page_size)
        if continuation_token is not None:
            params["continuationToken"] = continuation_token

        url = f"v3/conversations/{conversation_id}/pagedmembers"

        async with self.client.get(url, params=params) as response:
            if response.status >= 400:
                logger.error(
                    f"Error getting conversation paged members: {response.status}"
                )
                response.raise_for_status()

            data = await response.json()
            return PagedMembersResult.model_validate(data)

    async def send_conversation_history(
        self, conversation_id: str, body: Any
    ) -> ResourceResponse:
        """
        Sends conversation history to a conversation.

        :param conversation_id: The ID of the conversation.
        :param body: The conversation history.
        :return: The resource response.
        """
        if not conversation_id:
            raise ValueError("conversationId is required")

        url = f"v3/conversations/{conversation_id}/activities/history"

        async with self.client.post(url, json=body) as response:
            if (
                response.status >= 400
                and response.status != 201
                and response.status != 202
            ):
                logger.error(f"Error sending conversation history: {response.status}")
                response.raise_for_status()

            data = await response.json()
            return ResourceResponse.model_validate(data)


class ConnectorClient(ConnectorClientBase):
    """
    ConnectorClient is a client for interacting with the Microsoft M365 Agents SDK Connector API.
    """

    def __init__(self, endpoint: str, token: str, *, session: ClientSession = None):
        """
        Initialize a new instance of ConnectorClient.

        :param session: The aiohttp ClientSession to use for HTTP requests.
        """
        if not endpoint.endswith("/"):
            endpoint += "/"

        # Configure headers with JSON acceptance
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Create session with the base URL
        session = session or ClientSession(
            base_url=endpoint,
            headers=headers,
        )

        if len(token) > 1:
            session.headers.update({"Authorization": f"Bearer {token}"})

        self.client = session
        self._attachments = AttachmentsOperations(
            self.client
        )  # Will implement if needed
        self._conversations = ConversationsOperations(
            self.client
        )  # Will implement if needed

    @property
    def base_uri(self) -> str:
        """
        Gets the base URI for the client.

        :return: The base URI.
        """
        return str(self.client._base_url)

    @property
    def attachments(self) -> AttachmentsBase:
        """
        Gets the attachments operations.

        :return: The attachments operations.
        """
        return self._attachments

    @property
    def conversations(self) -> ConversationsBase:
        """
        Gets the conversations operations.

        :return: The conversations operations.
        """
        return self._conversations

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.client:
            await self.client.close()
