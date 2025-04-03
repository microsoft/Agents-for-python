from pydantic import BaseModel
from typing import Optional


class TaskModuleCardResponse(BaseModel):
    """Tab Response to 'task/submit' from a tab.

    :param value: The JSON for the Adaptive cards to appear in the tab.
    :type value: TabResponse
    """

    value: Optional["TabResponse"]
