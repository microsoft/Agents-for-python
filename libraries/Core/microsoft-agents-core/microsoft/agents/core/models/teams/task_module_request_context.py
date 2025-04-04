from pydantic import BaseModel
from typing import Optional


class TaskModuleRequestContext(BaseModel):
    """Context for a task module request.

    :param theme: The current user's theme.
    :type theme: Optional[str]
    """

    theme: Optional[str]
