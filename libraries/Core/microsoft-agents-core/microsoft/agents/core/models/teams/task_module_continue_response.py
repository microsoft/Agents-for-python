# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import Optional
from .task_module_task_info import TaskModuleTaskInfo


class TaskModuleContinueResponse(BaseModel):
    """Response to continue a task module.

    :param type: The type of response. Default is 'continue'.
    :type type: str
    :param value: The task module task info.
    :type value: Optional["TaskModuleTaskInfo"]
    """

    type: str = None
    value: Optional[TaskModuleTaskInfo] = None
