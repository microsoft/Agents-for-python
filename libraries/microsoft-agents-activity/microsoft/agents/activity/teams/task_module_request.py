# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Any, Optional

from .task_module_request_context import TaskModuleRequestContext
from .tab_entity_context import TabEntityContext


class TaskModuleRequest(AgentsModel):
    """Task module invoke request value payload.

    :param data: User input data. Free payload with key-value pairs.
    :type data: object
    :param context: Current user context, i.e., the current theme
    :type context: Optional[Any]
    :param tab_entity_context: Gets or sets current tab request context.
    :type tab_entity_context: Optional[TabEntityContext]
    """

    data: Optional[Any]
    context: Optional[TaskModuleRequestContext]
    tab_entity_context: Optional[TabEntityContext] = Field(None, alias="tabContext")
