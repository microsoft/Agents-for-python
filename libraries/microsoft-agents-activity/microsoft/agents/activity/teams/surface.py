from ..agents_model import AgentsModel
from enum import Enum


class SurfaceType(int, Enum):
    UNKNOWN = 0
    MEETING_STAGE = 1
    MEETING_TAB_ICON = 2


class Surface(AgentsModel):
    """Specifies where the notification will be rendered in the meeting UX.

    :param type: The value indicating where the notification will be rendered in the meeting UX.
    :type type: SurfaceType
    """

    type: SurfaceType
