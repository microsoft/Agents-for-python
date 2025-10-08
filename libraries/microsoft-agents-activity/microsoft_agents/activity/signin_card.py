# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class SigninCard(AgentsModel):
    """A card representing a request to sign in.

    :param text: Text for signin request
    :type text: str
    :param buttons: Action to use to perform signin
    :type buttons: list[~microsoft_agents.activity.CardAction]
    """

    text: str = None
    buttons: list[CardAction] = None
