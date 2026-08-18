# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .attachment import Attachment
from .card import Card
from .card_action import CardAction
from .content_types import ContentTypes
from ._type_aliases import NonEmptyString


class SigninCard(Card):
    """A card representing a request to sign in.

    :param text: Text for signin request
    :type text: str
    :param buttons: Action to use to perform signin
    :type buttons: list[~microsoft_agents.activity.CardAction]
    """

    text: str = None
    buttons: list[CardAction] = None

    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        :returns: The generated attachment.
        """
        return Attachment(content_type=ContentTypes.signin_card, content=self)
