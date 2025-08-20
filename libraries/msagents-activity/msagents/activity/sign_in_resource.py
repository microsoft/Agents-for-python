from ._type_aliases import NonEmptyString
from .agents_model import AgentsModel
from .token_exchange_resource import TokenExchangeResource
from .token_post_resource import TokenPostResource


class SignInResource(AgentsModel):
    """
    A type containing information for single sign-on.
    """

    sign_in_link: NonEmptyString = None
    token_exchange_resource: TokenExchangeResource = None
    token_post_resource: TokenPostResource = None
