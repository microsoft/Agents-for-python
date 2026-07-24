# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import AgentsModel, ConversationReference


class AgentConversationReference(AgentsModel):
    conversation_reference: ConversationReference
    oauth_scope: str
