from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class SigninCard(AgentsModel):
    """A card representing a request to sign in.

    :param text: Text for signin request
    :type text: str
    :param buttons: Action to use to perform signin
    :type buttons: list[~microsoft.agents.protocols.models.CardAction]
    """

    text: NonEmptyString = None
    buttons: list[CardAction] = None
