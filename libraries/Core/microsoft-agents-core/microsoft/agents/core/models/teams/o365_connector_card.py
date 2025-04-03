from pydantic import BaseModel
from typing import List, Optional


class O365ConnectorCard(BaseModel):
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

    title: str
    text: Optional[str]
    summary: Optional[str]
    theme_color: Optional[str]
    sections: Optional[List["O365ConnectorCardSection"]]
    potential_action: Optional[List["O365ConnectorCardActionBase"]]
