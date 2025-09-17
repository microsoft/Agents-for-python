from typing import Type, TypeVar

from .targeted_meeting_notification import TargetedMeetingNotification

MeetingNotification = TypeVar("MeetingNotification", bound=TargetedMeetingNotification)