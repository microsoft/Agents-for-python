from microsoft.agents.activity import AgentsModel, ConversationReference


class AgentConversationReference(AgentsModel):
    conversation_reference: ConversationReference
    oauth_scope: str
