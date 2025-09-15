from microsoft_agnets.activity import AgentsModel

class MessagingExtensionQueryOptions(AgentsModel):
    skip: Optional[int] = None
    count: Optional[int] = None