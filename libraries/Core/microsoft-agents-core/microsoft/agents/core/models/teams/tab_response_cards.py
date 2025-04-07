# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.from pydantic import BaseModel

from pydantic import BaseModel
from typing import List

from .tab_response_card import TabResponseCard


class TabResponseCards(BaseModel):
    """Envelope for cards for a TabResponse.

    :param cards: Gets or sets adaptive card for this card tab response.
    :type cards: list[TabResponseCard]
    """

    cards: List[TabResponseCard] = None
