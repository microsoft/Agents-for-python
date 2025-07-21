from microsoft.agents.activity import AgentsModel, Activity


class ExecuteTurnRequest(AgentsModel):

    activity: Activity
