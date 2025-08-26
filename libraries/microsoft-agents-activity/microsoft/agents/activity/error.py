from .inner_http_error import InnerHttpError
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class Error(AgentsModel):
    """Object representing error information.

    :param code: Error code
    :type code: str
    :param message: Error message
    :type message: str
    :param inner_http_error: Error from inner http call
    :type inner_http_error: ~microsoft.agents.protocols.models.InnerHttpError
    """

    code: NonEmptyString = None
    message: NonEmptyString = None
    inner_http_error: InnerHttpError = None
