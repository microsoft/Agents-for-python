from pydantic import BaseModel
from typing import Optional


class TabResponseCards(BaseModel):
    cards: list


class TabResponsePayload(BaseModel):
    """Initializes a new instance of the TabResponsePayload class.

    :param type: Gets or sets choice of action options when responding to the
     tab/fetch message. Possible values include: 'continue', 'auth' or 'silentAuth'
    :type type: str
    :param value: Gets or sets the TabResponseCards when responding to
     tab/fetch activity with type of 'continue'.
    :type value: TabResponseCards
    :param suggested_actions: Gets or sets the Suggested Actions for this card tab.
    :type suggested_actions: object
    """

    type: str
    value: Optional[TabResponseCards]
    suggested_actions: Optional[object]
