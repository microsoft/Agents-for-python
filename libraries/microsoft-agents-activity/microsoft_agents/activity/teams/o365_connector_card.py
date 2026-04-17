# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .o365_connector_card_section import O365ConnectorCardSection
from .o365_connector_card_action_base import O365ConnectorCardActionBase


class O365ConnectorCard(AgentsModel):
    """O365 connector card.

    :param title: Title of the item
    :type title: str
    :param text: Text for the card
    :type text: str | None
    :param summary: Summary for the card
    :type summary: str | None
    :param theme_color: Theme color for the card
    :type theme_color: str | None
    :param sections: Set of sections for the current card
    :type sections: list[O365ConnectorCardSection] | None
    :param potential_action: Set of actions for the current card
    :type potential_action: list[O365ConnectorCardActionBase] | None
    """

    title: str = None
    text: str | None = None
    summary: str | None = None
    theme_color: str | None = None
    sections: list[O365ConnectorCardSection] | None = None
    potential_action: list[O365ConnectorCardActionBase] | None = None
