from pydantic import BaseModel
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    UNKNOWN = "Unknown"
    TASK = "Task"


class MeetingStageSurface(BaseModel):
    """Specifies meeting stage surface.

    :param content_type: The content type of this MeetingStageSurface.
    :type content_type: ContentType
    :param content: The content of this MeetingStageSurface.
    :type content: Any
    """

    content_type: ContentType = ContentType.TASK
    content: Any
