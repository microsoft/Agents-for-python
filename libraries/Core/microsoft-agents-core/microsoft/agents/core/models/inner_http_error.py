from .agents_model import AgentsModel


class InnerHttpError(AgentsModel):
    """Object representing inner http error.

    :param status_code: HttpStatusCode from failed request
    :type status_code: int
    :param body: Body from failed request
    :type body: object
    """

    status_code: int = None
    body: object = None
