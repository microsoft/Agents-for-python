from pydantic import BaseModel
from typing import Optional


class TaskModuleResponse(BaseModel):
    """Response to a task module request.

    :param type: The type of response. Possible values include: 'continue', 'message'.
    :type type: str
    :param value: The task module response value.
    :type value: Optional[object]
    """

    type: str
    value: Optional[object]
