from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenRequest(AgentsModel):
    """A request to receive a user token.

    :param provider: The provider to request a user token from
    :type provider: str
    :param settings: A collection of settings for the specific provider for
     this request
    :type settings: dict[str, object]
    """

    provider: NonEmptyString = None
    settings: dict = None
