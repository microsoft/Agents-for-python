from pydantic import BaseModel
from typing import Optional


class MessagingExtensionActionResponse(BaseModel):
    """Response of messaging extension action.

    :param task: The JSON for the Adaptive card to appear in the task module.
    :type task: Optional["TaskModuleResponseBase"]
    :param compose_extension: The compose extension result.
    :type compose_extension: Optional["MessagingExtensionResult"]
    :param cache_info: CacheInfo for this MessagingExtensionActionResponse.
    :type cache_info: Optional["CacheInfo"]
    """

    task: Optional["TaskModuleResponseBase"]
    compose_extension: Optional["MessagingExtensionResult"]
    cache_info: Optional["CacheInfo"]
