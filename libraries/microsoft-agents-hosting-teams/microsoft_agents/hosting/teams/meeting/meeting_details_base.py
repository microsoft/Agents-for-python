from microsoft_agents.activity import AgentsModel

class MeetingDetailsBase(AgentsModel):
    id: str
    join_url: str
    title: str