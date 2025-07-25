"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging

from typing import Type

from microsoft.agents.hosting.core.storage import Storage, StoreItem

from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.state import AgentState

logger = logging.getLogger(__name__)


class ConversationState(AgentState):
    """
    Default Conversation State
    """

    CONTEXT_SERVICE_KEY = "ConversationState"

    def __init__(self, storage: Storage) -> None:
        """
        Initialize ConversationState with a key and optional properties.

        param storage: Storage instance to use for state management.
        type storage: Storage
        """
        super().__init__(storage=storage, context_service_key=self.CONTEXT_SERVICE_KEY)

    def get_storage_key(
        self, turn_context: TurnContext, *, target_cls: Type[StoreItem] = None
    ):
        channel_id = turn_context.activity.channel_id
        if not channel_id:
            logger.error("Invalid activity: missing channel_id.")
            raise ValueError("Invalid activity: missing channel_id.")

        conversation_id = turn_context.activity.conversation.id
        if not conversation_id:
            logger.error("Invalid activity: missing conversation_id.")
            raise ValueError("Invalid activity: missing conversation_id.")

        return f"{channel_id}/conversations/{conversation_id}"
