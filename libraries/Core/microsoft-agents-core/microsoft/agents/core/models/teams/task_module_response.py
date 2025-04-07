# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .task_module_response_base import TaskModuleResponseBase
from .cache_info import CacheInfo


class TaskModuleResponse(AgentsModel):
    """Envelope for Task Module Response.

    :param task: The JSON for the Adaptive card to appear in the task module.
    :type task: ~botframework.connector.teams.models.TaskModuleResponseBase
    :param cache_info: CacheInfo for this TaskModuleResponse.
    :type cache_info: ~botframework.connector.teams.models.CacheInfo
    """

    type: TaskModuleResponseBase = None
    cache_info: CacheInfo = None
