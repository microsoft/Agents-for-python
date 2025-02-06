from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class OAuthCard(AgentsModel):
    """A card representing a request to perform a sign in via OAuth.

    :param text: Text for signin request
    :type text: str
    :param connection_name: The name of the registered connection
    :type connection_name: str
    :param buttons: Action to use to perform signin
    :type buttons: list[~microsoft.agents.protocols.models.CardAction]
    """

    text: NonEmptyString = None
    connection_name: NonEmptyString = None
    buttons: list[CardAction] = None
    token_exchange_resource: object = None
