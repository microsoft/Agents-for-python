# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

from .attachment import Attachment
from .card import Card
from .content_types import ContentTypes
from ._type_aliases import NonEmptyString


class AdaptiveCardCard(Card):
    """A card that carries a raw Adaptive Card JSON payload.

    The JSON is stored verbatim in :attr:`content` and unpacked into the attachment as nested
    JSON when the activity is serialized.

    :param content: The Adaptive Card content as a JSON string.
    :type content: str
    """

    content: NonEmptyString = None

    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        The stored JSON string is parsed so that it is embedded as nested JSON in the attachment.

        :returns: The generated attachment.
        """
        return Attachment(
            content_type=ContentTypes.adaptive_card,
            content=json.loads(self.content),
        )
