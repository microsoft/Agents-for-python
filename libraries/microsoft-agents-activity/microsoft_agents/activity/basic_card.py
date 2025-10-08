# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from .card_image import CardImage
from .card_action import CardAction
from ._type_aliases import NonEmptyString


class BasicCard(AgentsModel):
    """A basic card.

    :param title: Title of the card
    :type title: str
    :param subtitle: Subtitle of the card
    :type subtitle: str
    :param text: Text for the card
    :type text: str
    :param images: Array of images for the card
    :type images: list[~microsoft_agents.activity.CardImage]
    :param buttons: Set of actions applicable to the current card
    :type buttons: list[~microsoft_agents.activity.CardAction]
    :param tap: This action will be activated when user taps on the card
     itself
    :type tap: ~microsoft_agents.activity.CardAction
    """

    title: NonEmptyString = None
    subtitle: NonEmptyString = None
    text: str = None
    images: list[CardImage] = None
    buttons: list[CardAction] = None
    tap: CardAction = None
