# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field

from .config_response import ConfigResponse
from .task_module_response_base import TaskModuleResponseBase


class ConfigTaskResponse(ConfigResponse):
    """Envelope for Config Task Response.

    This class uses TaskModuleResponseBase as the type for the config parameter.
    """

    config: TaskModuleResponseBase = Field(
        default_factory=lambda: TaskModuleResponseBase()
    )
