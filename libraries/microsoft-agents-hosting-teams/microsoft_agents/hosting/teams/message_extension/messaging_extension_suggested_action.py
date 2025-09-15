from typing import Optional

from microsoft_agents.activity import AgentsModel, CardAction

class MessagingExtensionSuggestedAction(AgentsModel):
    actions: Optional[list[CardAction]] = None