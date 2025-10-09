# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from .error import Error


class ErrorResponse(AgentsModel):
    """An HTTP API response.

    :param error: Error message
    :type error: ~microsoft_agents.activity.Error
    """

    error: Error = None
