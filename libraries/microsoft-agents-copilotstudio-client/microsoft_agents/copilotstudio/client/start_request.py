# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
from microsoft_agents.activity import AgentsModel
from pydantic import Field


class StartRequest(AgentsModel):
    """
    Request model for starting a conversation with Copilot Studio.
    """

    locale: Optional[str] = Field(
        default=None, description="The locale to use as defined by the client"
    )
    emit_start_conversation_event: bool = Field(
        default=True,
        alias="emitStartConversationEvent",
        description="Whether to emit a StartConversation event",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        alias="conversationId",
        description="Conversation ID requested by the client",
    )
