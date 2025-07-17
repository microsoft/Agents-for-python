from microsoft.agents.core.models import AgentsModel, Activity


class ExecuteTurnRequest(AgentsModel):

    activity: Activity
