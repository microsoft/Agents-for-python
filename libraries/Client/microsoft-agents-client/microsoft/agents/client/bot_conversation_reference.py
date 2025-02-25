from microsoft.agents.core.models import AgentsModel, ConversationReference


class BotConversationReference(AgentsModel):
    conversation_reference: ConversationReference
    oauth_scope: str
