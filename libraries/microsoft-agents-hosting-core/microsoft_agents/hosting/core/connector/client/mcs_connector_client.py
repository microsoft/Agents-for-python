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
from .connector_client import AttachmentOperations
from ..get_product_info import get_product_info


logger = logging.getLogger(__name__)

class MCSConversationsOperations(ConversationsBase):
    """Operations for managing conversations in MCS."""

    def __init__(self, client: ClientSession):
        self.client = client

    # async def create_conversation(self, body: ConversationParameters) -> ConversationResourceResponse:
    #     raise NotImplementedError()
    
    # async def delete_activity(self, conversation_id: str, activity_id: str) -> None:
    #     raise NotImplementedError()
    
    # async def delete_conversation_member(self, conversation_id: str, member_id: str) -> None:
    #     raise NotImplementedError()

    # async def get_activity_members(self, conversation_id: str, activity_id: str) -> list[ChannelAccount]:
    #     raise NotImplementedError()
    
    # async def get_conversation_member(self, conversation_id: str, member_id: str) -> ChannelAccount:
    #     raise NotImplementedError()
    
    # async def get_conversation_members(self, conversation_id: str) -> list[ChannelAccount]:
    #     raise NotImplementedError()
    
    # async def get_conversation_paged_members(
    #     self,
    #     conversation_id: str,
    #     page_size: Optional[int] = None,
    #     continuation_token: Optional[str] = None,
    # ) -> PagedMembersResult:
    #     raise NotImplementedError()
    
    async def send_to_conversation(self, conversation_id: str, activity: Activity) -> ResourceResponse:
        if not activity:
            raise ValueError("Activity cannot be None")

    # Implement conversation-related methods as needed

class MCSConnectorClient(ConnectorClientBase):

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
        self._conversations = MCSConversationsOperations(
            self.client
        )  # Will implement if needed