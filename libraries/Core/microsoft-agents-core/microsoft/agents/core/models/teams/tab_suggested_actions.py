# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import List

from ..card_action import CardAction


class TabSuggestedActions(BaseModel):
    """Tab SuggestedActions (Only when type is 'auth' or 'silentAuth').

    :param actions: Gets or sets adaptive card for this card tab response.
    :type actions: list[CardAction]
    """

    actions: List[CardAction] = None
