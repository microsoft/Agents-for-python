# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .task_module_task_info import TaskModuleTaskInfo


class TaskModuleContinueResponse(AgentsModel):
    """Response to continue a task module.

    :param type: The type of response. Default is 'continue'.
    :type type: str
    :param value: The task module task info.
    :type value: TaskModuleTaskInfo | None
    """

    type: str = None
    value: TaskModuleTaskInfo | None = None
