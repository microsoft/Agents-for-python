# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from pydantic import Field
from ..agents_model import AgentsModel

from .task_module_request_context import TaskModuleRequestContext
from .tab_entity_context import TabEntityContext


class TaskModuleRequest(AgentsModel):
    """Task module invoke request value payload.

    :param data: User input data. Free payload with key-value pairs.
    :type data: Any | None
    :param context: Current user context, i.e., the current theme
    :type context: TaskModuleRequestContext | None
    :param tab_entity_context: Gets or sets current tab request context.
    :type tab_entity_context: TabEntityContext | None
    """

    data: Any | None
    context: TaskModuleRequestContext | None
    tab_entity_context: TabEntityContext | None = Field(None, alias="tabContext")
