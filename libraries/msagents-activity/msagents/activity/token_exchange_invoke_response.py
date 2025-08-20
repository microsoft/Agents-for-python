from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenExchangeInvokeResponse(AgentsModel):
    """TokenExchangeInvokeResponse.

    :param id: The id from the OAuthCard.
    :type id: str
    :param connection_name: The connection name.
    :type connection_name: str
    :param failure_detail: The details of why the token exchange failed.
    :type failure_detail: str
    :param properties: Extension data for overflow of properties.
    :type properties: dict[str, object]
    """

    id: NonEmptyString = None
    connection_name: NonEmptyString = None
    failure_detail: NonEmptyString = None
    properties: dict = None
