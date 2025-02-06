from .agents_model import AgentsModel
from .error import Error


class ErrorResponse(AgentsModel):
    """An HTTP API response.

    :param error: Error message
    :type error: ~microsoft.agents.protocols.models.Error
    """

    error: Error = None
