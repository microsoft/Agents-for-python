# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .surface import Surface, SurfaceType


class MeetingTabIconSurface(Surface):
    """Specifies meeting tab icon surface.

    :param tab_entity_id: The tab entity Id of this MeetingTabIconSurface.
    :type tab_entity_id: str
    """

    type: SurfaceType = SurfaceType.MEETING_TAB_ICON
    tab_entity_id: str = None
