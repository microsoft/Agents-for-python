# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import List
from .o365_connector_card_input_base import O365ConnectorCardInputBase
from .o365_connector_card_action_base import O365ConnectorCardActionBase


class O365ConnectorCardActionCard(AgentsModel):
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

    type: str = Field(None, alias="@type")
    name: str = None
    id: str = Field(None, alias="@id")
    inputs: List[O365ConnectorCardInputBase] = None
    actions: List[O365ConnectorCardActionBase] = None
