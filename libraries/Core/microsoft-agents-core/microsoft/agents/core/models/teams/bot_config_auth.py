from pydantic import BaseModel
from typing import Optional


class BotConfigAuth(BaseModel):
    """Specifies bot config auth, including type and suggestedActions.

    :param type: The type of bot config auth.
    :type type: str
    :param suggested_actions: The suggested actions of bot config auth.
    :type suggested_actions: object
    """

    type: str = "auth"
    suggested_actions: Optional[object]
