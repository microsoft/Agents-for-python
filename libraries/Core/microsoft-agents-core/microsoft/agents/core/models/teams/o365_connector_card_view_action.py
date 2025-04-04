from pydantic import BaseModel
from typing import Optional


class O365ConnectorCardViewAction(BaseModel):
    """O365 connector card ViewAction action.

    :param type: Type of the action. Default is 'ViewAction'.
    :type type: str
    :param name: Name of the ViewAction action.
    :type name: str
    :param id: Id of the ViewAction action.
    :type id: str
    :param target: Target URL for the ViewAction action.
    :type target: Optional[str]
    """

    type: str = "ViewAction"
    name: str
    id: str
    target: Optional[str]
