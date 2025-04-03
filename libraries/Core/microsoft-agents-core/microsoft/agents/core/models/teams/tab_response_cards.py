from pydantic import BaseModel
from typing import List


class TabResponseCard(BaseModel):
    card: object


class TabResponseCards(BaseModel):
    """Envelope for cards for a TabResponse.

    :param cards: Gets or sets adaptive card for this card tab response.
    :type cards: list[TabResponseCard]
    """

    cards: List[TabResponseCard]
