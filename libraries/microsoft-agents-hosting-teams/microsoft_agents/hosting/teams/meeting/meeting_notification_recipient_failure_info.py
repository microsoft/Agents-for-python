from agents import Agent
from microsoft_agents.activity import AgentsModel

class MeetingNotificationRecipientFailureInfo(AgentsModel):
    recipient_mri: str
    failure_reason: str
    error_code: str