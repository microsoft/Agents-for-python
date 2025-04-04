from pydantic import BaseModel


class TaskModuleResponseBase(BaseModel):
    """Base class for task module responses.

    :param type: The type of response.
    :type type: str
    """

    type: str
