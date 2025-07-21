# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol, Optional

from microsoft.agents.activity import (
    AttachmentInfo,
    ConversationResourceResponse,
    ConversationsResult,
    ConversationParameters,
    ResourceResponse,
    Activity,
    Transcript,
    ChannelAccount,
    PagedMembersResult,
    AttachmentData,
)


class ConversationsBase(Protocol):
    @abstractmethod
    async def get_conversations(
        self, continuation_token: Optional[str] = None
    ) -> ConversationsResult:
        """
        List the Conversations in which this agent has participated.
        """
        raise NotImplementedError()

    @abstractmethod
    async def create_conversation(
        self, parameters: ConversationParameters
    ) -> ConversationResourceResponse:
        """
        Create a new Conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_to_conversation(
        self, conversation_id: str, activity: Activity
    ) -> ResourceResponse:
        """
        Send an activity to the end of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_conversation_history(
        self, conversation_id: str, transcript: Transcript
    ) -> ResourceResponse:
        """
        Upload the historic activities to the conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_activity(
        self, conversation_id: str, activity_id: str, activity: Activity
    ) -> ResourceResponse:
        """
        Edit an existing activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def reply_to_activity(
        self, conversation_id: str, activity_id: str, activity: Activity
    ) -> ResourceResponse:
        """
        Reply to an activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_activity(self, conversation_id: str, activity_id: str):
        """
        Delete an existing activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_conversation_members(
        self, conversation_id: str
    ) -> list[ChannelAccount]:
        """
        Enumerate the members of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_conversation_member(
        self, conversation_id: str, user_id: str
    ) -> ChannelAccount:
        """
        Enumerate the members of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_conversation_paged_members(
        self,
        conversation_id: str,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> PagedMembersResult:
        """
        Enumerate the members of a conversation one page at a time.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_conversation_member(self, conversation_id: str, member_id: str):
        """
        Deletes a member from a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_activity_members(
        self, conversation_id: str, activity_id: str
    ) -> list[ChannelAccount]:
        """
        Enumerate the members of an activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def upload_attachment(
        self, conversation_id: str, attachment_upload: AttachmentData
    ) -> ResourceResponse:
        """
        Upload an attachment directly into a channel's storage.
        """
        raise NotImplementedError()
