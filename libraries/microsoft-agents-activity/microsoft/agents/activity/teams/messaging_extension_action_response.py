# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .task_module_response_base import TaskModuleResponseBase
from .messaging_extension_result import MessagingExtensionResult
from .cache_info import CacheInfo


class MessagingExtensionActionResponse(AgentsModel):
    """Response of messaging extension action.

    :param task: The JSON for the Adaptive card to appear in the task module.
    :type task: "TaskModuleResponseBase"
    :param compose_extension: The compose extension result.
    :type compose_extension: "MessagingExtensionResult"
    :param cache_info: CacheInfo for this MessagingExtensionActionResponse.
    :type cache_info: "CacheInfo"
    """

    task: TaskModuleResponseBase = None
    compose_extension: MessagingExtensionResult = None
    cache_info: CacheInfo = None
