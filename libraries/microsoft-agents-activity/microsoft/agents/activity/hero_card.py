from .card_action import CardAction
from .card_image import CardImage
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class HeroCard(AgentsModel):
    """A Hero card (card with a single, large image).

    :param title: Title of the card
    :type title: str
    :param subtitle: Subtitle of the card
    :type subtitle: str
    :param text: Text for the card
    :type text: str
    :param images: Array of images for the card
    :type images: list[~microsoft.agents.protocols.models.CardImage]
    :param buttons: Set of actions applicable to the current card
    :type buttons: list[~microsoft.agents.protocols.models.CardAction]
    :param tap: This action will be activated when user taps on the card
     itself
    :type tap: ~microsoft.agents.protocols.models.CardAction
    """

    title: NonEmptyString = None
    subtitle: NonEmptyString = None
    text: NonEmptyString = None
    images: list[CardImage] = None
    buttons: list[CardAction] = None
    tap: CardAction = None
