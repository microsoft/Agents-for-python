from typing import Type, Union, TypeVar

from .meeting_stage_surface import MeetingStageSurface
from .meeting_tab_icon_surface import MeetingTabIconSurface

# robrandao: TODO -> generic
MeetingSurface = TypeVar("MeetingSurface", Union[MeetingStageSurface, MeetingTabIconSurface])