from pydantic import BaseModel
from typing import Optional
from .config_response import ConfigResponse


class ConfigTaskResponse(ConfigResponse):
    """Envelope for Config Task Response.

    This class uses TaskModuleResponseBase as the type for the config parameter.
    """

    config: Optional["TaskModuleResponseBase"] = None
