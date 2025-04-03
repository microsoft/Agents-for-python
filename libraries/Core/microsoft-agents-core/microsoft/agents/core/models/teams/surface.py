from pydantic import BaseModel
from enum import Enum


class SurfaceType(str, Enum):
    UNKNOWN = "Unknown"
    MEETING_STAGE = "MeetingStage"
    MEETING_TAB_ICON = "MeetingTabIcon"


class Surface(BaseModel):
    """Specifies where the notification will be rendered in the meeting UX.

    :param type: The value indicating where the notification will be rendered in the meeting UX.
    :type type: SurfaceType
    """

    type: SurfaceType
