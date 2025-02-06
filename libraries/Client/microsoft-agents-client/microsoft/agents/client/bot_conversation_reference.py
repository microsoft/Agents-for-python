from microsoft.agents.core.models import ConversationReference


class BotConversationReference:
    def __init__(self, conversation_reference: ConversationReference, oauth_scope: str):
        self.conversation_reference = conversation_reference
        self.oauth_scope = oauth_scope
