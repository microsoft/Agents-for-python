from pydantic import BaseModel
from typing import Optional
from .config_response_base import ConfigResponseBase


class ConfigResponse(ConfigResponseBase):
    """Envelope for Config Response Payload.

    :param config: The response to the config message. Possible values: 'auth', 'task'
    :type config: object
    :param cache_info: Response cache info
    :type cache_info: object
    """

    config: Optional[object]
    cache_info: Optional[object]
