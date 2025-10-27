# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Connector Client for Microsoft Agents."""

import logging
from typing import Any, Optional
from aiohttp import ClientSession
from io import BytesIO

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    ConversationParameters,
    ConversationResourceResponse,
    ResourceResponse,
    ConversationsResult,
    PagedMembersResult,
)
from microsoft_agents.hosting.core.connector import ConnectorClientBase
from ..attachments_base import AttachmentsBase
from ..conversations_base import ConversationsBase
from ..get_product_info import get_product_info


logger = logging.getLogger(__name__)


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

        logger.info("Getting attachment info for ID: %s", attachment_id)
        async with self.client.get(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting attachment info: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "AttachmentsOperations.get_attachment(): attachmentId is required",
                stack_info=True,
            )
            raise ValueError("attachmentId is required")
        if view_id is None:
            logger.error(
                "AttachmentsOperations.get_attachment(): viewId is required",
                stack_info=True,
            )
            raise ValueError("viewId is required")

        url = f"v3/attachments/{attachment_id}/views/{view_id}"

        logger.info(
            "Getting attachment for ID: %s, View ID: %s", attachment_id, view_id
        )
        async with self.client.get(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting attachment: %s", response.status, stack_info=True
                )
                response.raise_for_status()

            data = await response.read()
            return BytesIO(data)


class ConversationsOperations(ConversationsBase):

    def __init__(self, client: ClientSession, **kwargs):
        self.client = client
        self._max_conversation_id_length = kwargs.get("max_conversation_id_length", 150)

    def _normalize_conversation_id(self, conversation_id: str) -> str:
        return conversation_id[: self._max_conversation_id_length]

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

        logger.info(
            "Getting conversations with continuation token: %s", continuation_token
        )
        async with self.client.get("v3/conversations", params=params) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting conversations: %s", response.status, stack_info=True
                )
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

        logger.info("Creating a new conversation")
        async with self.client.post(
            "v3/conversations",
            json=body.model_dump(by_alias=True, exclude_unset=True, mode="json"),
        ) as response:
            if response.status >= 300:
                logger.error(
                    "Error creating conversation: %s", response.status, stack_info=True
                )
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
            logger.error(
                "ConversationsOperations.reply_to_activity(): conversationId and activityId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and activityId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        logger.info(
            "Replying to activity: %s in conversation: %s. Activity type is %s",
            activity_id,
            conversation_id,
            body.type,
        )

        async with self.client.post(
            url,
            json=body.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
            ),
        ) as response:
            result = await response.json() if response.content_length else {}

            if response.status >= 300:
                logger.error(
                    "Error replying to activity: %s",
                    result or response.status,
                    stack_info=True,
                )
                response.raise_for_status()

            logger.info(
                "Reply to conversation/activity: %s, %s", result.get("id"), activity_id
            )

        return ResourceResponse.model_validate(result)

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
            logger.error(
                "ConversationsOperations.sent_to_conversation(): conversationId is required",
                stack_info=True,
            )
            raise ValueError("conversationId is required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities"

        logger.info(
            "Sending to conversation: %s. Activity type is %s",
            conversation_id,
            body.type,
        )
        async with self.client.post(
            url,
            json=body.model_dump(by_alias=True, exclude_unset=True, mode="json"),
        ) as response:
            if response.status >= 300:
                logger.error(
                    "Error sending to conversation: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "ConversationsOperations.update_activity(): conversationId and activityId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and activityId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        logger.info(
            "Updating activity: %s in conversation: %s. Activity type is %s",
            activity_id,
            conversation_id,
            body.type,
        )
        async with self.client.put(
            url,
            json=body.model_dump(by_alias=True, exclude_unset=True),
        ) as response:
            if response.status >= 300:
                logger.error(
                    "Error updating activity: %s", response.status, stack_info=True
                )
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
            logger.error(
                "ConversationsOperations.delete_activity(): conversationId and activityId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and activityId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities/{activity_id}"

        logger.info(
            "Deleting activity: %s from conversation: %s",
            activity_id,
            conversation_id,
        )
        async with self.client.delete(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error deleting activity: %s", response.status, stack_info=True
                )
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
            logger.error(
                "ConversationsOperations.upload_attachment(): conversationId is required",
                stack_info=True,
            )
            raise ValueError("conversationId is required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/attachments"

        # Convert the AttachmentData to a dictionary
        attachment_dict = {
            "name": body.name,
            "originalBase64": body.original_base64,
            "type": body.type,
            "thumbnailBase64": body.thumbnail_base64,
        }

        logger.info(
            "Uploading attachment to conversation: %s, Attachment name: %s",
            conversation_id,
            body.name,
        )
        async with self.client.post(url, json=attachment_dict) as response:
            if response.status >= 300:
                logger.error(
                    "Error uploading attachment: %s", response.status, stack_info=True
                )
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
            logger.error(
                "ConversationsOperations.get_conversation_members(): conversationId is required",
                stack_info=True,
            )
            raise ValueError("conversationId is required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/members"

        logger.info(
            "Getting conversation members for conversation: %s", conversation_id
        )
        async with self.client.get(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting conversation members: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "ConversationsOperations.get_conversation_member(): conversationId and memberId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and memberId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/members/{member_id}"

        logger.info(
            "Getting conversation member: %s from conversation: %s",
            member_id,
            conversation_id,
        )
        async with self.client.get(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting conversation member: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "ConversationsOperations.delete_conversation_member(): conversationId and memberId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and memberId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/members/{member_id}"

        logger.info(
            "Deleting conversation member: %s from conversation: %s",
            member_id,
            conversation_id,
        )
        async with self.client.delete(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error deleting conversation member: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "ConversationsOperations.get_activity_members(): conversationId and activityId are required",
                stack_info=True,
            )
            raise ValueError("conversationId and activityId are required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities/{activity_id}/members"

        logger.info(
            "Getting activity members for conversation: %s, Activity ID: %s",
            conversation_id,
            activity_id,
        )
        async with self.client.get(url) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting activity members: %s",
                    response.status,
                    stack_info=True,
                )
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
            logger.error(
                "ConversationsOperations.get_conversation_paged_members(): conversationId is required",
                stack_info=True,
            )
            raise ValueError("conversationId is required")

        params = {}
        if page_size is not None:
            params["pageSize"] = str(page_size)
        if continuation_token is not None:
            params["continuationToken"] = continuation_token

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/pagedmembers"

        logger.info(
            "Getting paged members for conversation: %s, Page Size: %s, Continuation Token: %s",
            conversation_id,
            page_size,
            continuation_token,
        )
        async with self.client.get(url, params=params) as response:
            if response.status >= 300:
                logger.error(
                    "Error getting conversation paged members: %s",
                    response.status,
                    stack_info=True,
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
            logger.error(
                "ConversationsOperations.send_conversation_history(): conversationId is required",
                stack_info=True,
            )
            raise ValueError("conversationId is required")

        conversation_id = self._normalize_conversation_id(conversation_id)
        url = f"v3/conversations/{conversation_id}/activities/history"

        logger.info("Sending conversation history to conversation: %s", conversation_id)
        async with self.client.post(url, json=body) as response:
            if response.status >= 300:
                logger.error(
                    "Error sending conversation history: %s",
                    response.status,
                    stack_info=True,
                )
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
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": get_product_info(),
        }
        # Create session with the base URL
        session = session or ClientSession(
            base_url=endpoint,
            headers=headers,
        )
        logger.debug(
            "ConnectorClient initialized with endpoint: %s and headers: %s",
            endpoint,
            headers,
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
            logger.debug("Closing ConnectorClient session")
            await self.client.close()
