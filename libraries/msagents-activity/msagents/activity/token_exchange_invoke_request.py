from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenExchangeInvokeRequest(AgentsModel):
    """TokenExchangeInvokeRequest.

    :param id: The id from the OAuthCard.
    :type id: str
    :param connection_name: The connection name.
    :type connection_name: str
    :param token: The user token that can be exchanged.
    :type token: str
    :param properties: Extension data for overflow of properties.
    :type properties: dict[str, object]
    """

    id: NonEmptyString = None
    connection_name: NonEmptyString = None
    token: NonEmptyString = None
    properties: dict = None
