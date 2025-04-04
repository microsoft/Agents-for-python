from pydantic import BaseModel
from typing import List


class O365ConnectorCardOpenUri(BaseModel):
    """O365 connector card OpenUri action.

    :param type: Type of the action. Default is 'OpenUri'.
    :type type: str
    :param name: Name of the OpenUri action.
    :type name: str
    :param id: Id of the OpenUri action.
    :type id: str
    :param targets: List of targets for the OpenUri action.
    :type targets: List["O365ConnectorCardOpenUriTarget"]
    """

    type: str = "OpenUri"
    name: str
    id: str
    targets: List["O365ConnectorCardOpenUriTarget"]
