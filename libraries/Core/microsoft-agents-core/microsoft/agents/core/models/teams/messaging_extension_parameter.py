from pydantic import BaseModel
from typing import Any


class MessagingExtensionParameter(BaseModel):
    """Messaging extension query parameters.

    :param name: Name of the parameter
    :type name: str
    :param value: Value of the parameter
    :type value: Any
    """

    name: str
    value: Any
