from pydantic import BaseModel
from typing import Optional


class TaskModuleContinueResponse(BaseModel):
    """Response to continue a task module.

    :param type: The type of response. Default is 'continue'.
    :type type: str
    :param value: The task module task info.
    :type value: Optional["TaskModuleTaskInfo"]
    """

    type: str = "continue"
    value: Optional["TaskModuleTaskInfo"]
