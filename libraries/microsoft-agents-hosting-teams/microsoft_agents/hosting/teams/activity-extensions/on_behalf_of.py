from microsoft_agents.activity import AgentsModel

class OnBehalfOf(AgentsModel):
    item_id: int
    mention_type: str
    mri: str
    display_name: Optional[str] = None