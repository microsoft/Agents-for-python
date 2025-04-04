from pydantic import BaseModel
from typing import Optional


class ConfigAuthResponse(BaseModel):
    """Response for configuration authentication.

    :param suggested_actions: Suggested actions for the configuration authentication.
    :type suggested_actions: Optional[object]
    """

    suggested_actions: Optional[object]
