# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .card_image import CardImage
from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ReceiptItem(AgentsModel):
    """An item on a receipt card.

    :param title: Title of the Card
    :type title: str
    :param subtitle: Subtitle appears just below Title field, differs from
     Title in font styling only
    :type subtitle: str
    :param text: Text field appears just below subtitle, differs from Subtitle
     in font styling only
    :type text: str
    :param image: Image
    :type image: ~microsoft_agents.activity.CardImage
    :param price: Amount with currency
    :type price: str
    :param quantity: Number of items of given kind
    :type quantity: str
    :param tap: This action will be activated when user taps on the Item
     bubble.
    :type tap: ~microsoft_agents.activity.CardAction
    """

    title: NonEmptyString = None
    subtitle: NonEmptyString = None
    text: str = None
    image: CardImage = None
    price: NonEmptyString = None
    quantity: NonEmptyString = None
    tap: CardAction = None
