from abc import abstractmethod
from typing import Protocol, Optional

from microsoft.agents.activity import (
    Activity,
    AttachmentData,
    ChannelAccount,
    ConversationResourceResponse,
    ConversationsResult,
    ConversationParameters,
    ResourceResponse,
    PagedMembersResult,
    Transcript,
)

from microsoft.agents.hosting.core.authorization import ClaimsIdentity


class ChannelApiHandlerProtocol(Protocol):
    @abstractmethod
    async def on_get_conversations(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        continuation_token: Optional[str] = None,
    ) -> ConversationsResult:
        """
        List the Conversations in which this agent has participated.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_create_conversation(
        self, claims_identity: ClaimsIdentity, parameters: ConversationParameters
    ) -> ConversationResourceResponse:
        """
        Create a new Conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_send_to_conversation(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity: Activity
    ) -> ResourceResponse:
        """
        Send an activity to the end of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_send_conversation_history(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        transcript: Transcript,
    ) -> ResourceResponse:
        """
        Upload the historic activities to the conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_update_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
    ) -> ResourceResponse:
        """
        Edit an existing activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_reply_to_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
    ) -> ResourceResponse:
        """
        Reply to an activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_delete_activity(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity_id: str
    ):
        """
        Delete an existing activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_get_conversation_members(
        self, claims_identity: ClaimsIdentity, conversation_id: str
    ) -> list[ChannelAccount]:
        """
        Enumerate the members of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_get_conversation_member(
        self,
        claims_identity: ClaimsIdentity,
        user_id: str,
        conversation_id: str,
    ) -> ChannelAccount:
        """
        Enumerate the members of a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_get_conversation_paged_members(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> PagedMembersResult:
        """
        Enumerate the members of a conversation one page at a time.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_delete_conversation_member(
        self, claims_identity: ClaimsIdentity, conversation_id: str, member_id: str
    ):
        """
        Deletes a member from a conversation.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_get_activity_members(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity_id: str
    ) -> list[ChannelAccount]:
        """
        Enumerate the members of an activity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_upload_attachment(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        attachment_upload: AttachmentData,
    ) -> ResourceResponse:
        """
        Upload an attachment directly into a channel's storage.
        """
        raise NotImplementedError()
