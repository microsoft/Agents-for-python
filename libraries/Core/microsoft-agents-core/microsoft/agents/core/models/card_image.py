from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class CardImage(AgentsModel):
    """An image on a card.

    :param url: URL thumbnail image for major content property
    :type url: str
    :param alt: Image description intended for screen readers
    :type alt: str
    :param tap: Action assigned to specific Attachment
    :type tap: ~microsoft.agents.protocols.models.CardAction
    """

    url: NonEmptyString = None
    alt: NonEmptyString = None
    tap: CardAction = None
