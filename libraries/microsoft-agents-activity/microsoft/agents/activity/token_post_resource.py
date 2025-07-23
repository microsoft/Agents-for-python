from .agents_model import AgentsModel

from ._type_aliases import NonEmptyString


class TokenPostResource(AgentsModel):
    """
    A type containing information for token posting.
    """

    sas_url: NonEmptyString = None
