# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List

from ..card_action import CardAction


class TabSuggestedActions(AgentsModel):
    """Tab SuggestedActions (Only when type is 'auth' or 'silentAuth').

    :param actions: Gets or sets adaptive card for this card tab response.
    :type actions: list[CardAction]
    """

    actions: List[CardAction] = None
