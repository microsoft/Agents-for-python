# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum

from .surface import Surface, SurfaceType


class ContentType(int, Enum):
    UNKNOWN = 0
    TASK = 1


class MeetingStageSurface(Surface):
    """Specifies meeting stage surface.

    :param content_type: The content type of this MeetingStageSurface.
    :type content_type: ContentType
    :param content: The content of this MeetingStageSurface.
    :type content: Any
    """

    type: SurfaceType = SurfaceType.MEETING_STAGE
    content_type: ContentType = ContentType.TASK
    content: object = None
