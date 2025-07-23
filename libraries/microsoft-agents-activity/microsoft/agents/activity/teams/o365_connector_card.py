# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List, Optional
from .o365_connector_card_section import O365ConnectorCardSection
from .o365_connector_card_action_base import O365ConnectorCardActionBase


class O365ConnectorCard(AgentsModel):
    """O365 connector card.

    :param title: Title of the item
    :type title: str
    :param text: Text for the card
    :type text: Optional[str]
    :param summary: Summary for the card
    :type summary: Optional[str]
    :param theme_color: Theme color for the card
    :type theme_color: Optional[str]
    :param sections: Set of sections for the current card
    :type sections: Optional[List["O365ConnectorCardSection"]]
    :param potential_action: Set of actions for the current card
    :type potential_action: Optional[List["O365ConnectorCardActionBase"]]
    """

    title: str = None
    text: Optional[str] = None
    summary: Optional[str] = None
    theme_color: Optional[str] = None
    sections: Optional[List[O365ConnectorCardSection]] = None
    potential_action: Optional[List[O365ConnectorCardActionBase]] = None
