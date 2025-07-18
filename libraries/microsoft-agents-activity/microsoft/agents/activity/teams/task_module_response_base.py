# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import ConfigDict
from ..agents_model import AgentsModel


class TaskModuleResponseBase(AgentsModel):
    """Base class for task module responses.

    :param type: The type of response.
    :type type: str
    """

    model_config = ConfigDict(extra="allow")

    type: str = None
