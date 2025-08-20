from .agents_model import AgentsModel
from .error import Error


class ErrorResponse(AgentsModel):
    """An HTTP API response.

    :param error: Error message
    :type error: ~msagents.protocols.models.Error
    """

    error: Error = None
