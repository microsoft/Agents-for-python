from pydantic import BaseModel
from typing import List


class O365ConnectorCardActionCard(BaseModel):
    """O365 connector card ActionCard action.

    :param type: Type of the action. Possible values include: 'ViewAction', 'OpenUri', 'HttpPOST', 'ActionCard'
    :type type: str
    :param name: Name of the action that will be used as button title
    :type name: str
    :param id: Action Id
    :type id: str
    :param inputs: Set of inputs contained in this ActionCard
    :type inputs: List["O365ConnectorCardInputBase"]
    :param actions: Set of actions contained in this ActionCard
    :type actions: List["O365ConnectorCardActionBase"]
    """

    type: str
    name: str
    id: str
    inputs: List["O365ConnectorCardInputBase"]
    actions: List["O365ConnectorCardActionBase"]
