from typing import Optional

from microsoft_agents.activity import AgentsModel

from .meeting_notification_recipient_failure_info import MeetingNotificationRecipientFailureInfo

class MeetingNotificationResponse(AgentsModel):
    recipients_failure_info: Optional[list[MeetingNotificationRecipientFailureInfo]] = None