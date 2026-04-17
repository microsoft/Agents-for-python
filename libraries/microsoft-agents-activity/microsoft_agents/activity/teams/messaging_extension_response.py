# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .messaging_extension_result import MessagingExtensionResult
from .cache_info import CacheInfo


class MessagingExtensionResponse(AgentsModel):
    """Messaging extension response.

    :param compose_extension: The compose extension result.
    :type compose_extension: MessagingExtensionResult | None
    :param cache_info: CacheInfo for this MessagingExtensionResponse.
    :type cache_info: CacheInfo | None
    """

    compose_extension: MessagingExtensionResult | None = None
    cache_info: CacheInfo | None = None
