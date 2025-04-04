from pydantic import BaseModel
from typing import Optional


class O365ConnectorCardHttpPOST(BaseModel):
    """O365 connector card HttpPOST action.

    :param type: Type of the action. Default is 'HttpPOST'.
    :type type: str
    :param name: Name of the HttpPOST action.
    :type name: str
    :param id: Id of the HttpPOST action.
    :type id: str
    :param body: Content of the HttpPOST action.
    :type body: Optional[str]
    """

    type: str = "HttpPOST"
    name: str
    id: str
    body: Optional[str]
