# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional

from .messaging_extension_result import MessagingExtensionResult
from .cache_info import CacheInfo


class MessagingExtensionResponse(AgentsModel):
    """Messaging extension response.

    :param compose_extension: The compose extension result.
    :type compose_extension: Optional["MessagingExtensionResult"]
    :param cache_info: CacheInfo for this MessagingExtensionResponse.
    :type cache_info: Optional["CacheInfo"]
    """

    compose_extension: Optional[MessagingExtensionResult] = None
    cache_info: Optional[CacheInfo] = None
