from pydantic import BaseModel
from typing import Optional


class TabResponse(BaseModel):
    """Response to a tab request.

    :param type: The type of response. Possible values include: 'continue', 'auth', 'silentAuth'.
    :type type: str
    :param value: The value of the tab response.
    :type value: Optional[object]
    """

    type: str
    value: Optional[object]
