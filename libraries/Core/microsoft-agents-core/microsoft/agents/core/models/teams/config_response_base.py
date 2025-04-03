from pydantic import BaseModel


class ConfigResponseBase(BaseModel):
    """Specifies Invoke response base, including response type.

    :param response_type: Response type for invoke request
    :type response_type: str
    """

    response_type: str
