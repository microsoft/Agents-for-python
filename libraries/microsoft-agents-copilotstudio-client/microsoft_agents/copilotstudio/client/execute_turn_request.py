from microsoft_agents.activity import AgentsModel, Activity


class ExecuteTurnRequest(AgentsModel):

    activity: Activity
