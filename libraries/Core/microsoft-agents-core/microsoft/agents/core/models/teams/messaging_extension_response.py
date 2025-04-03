from pydantic import BaseModel
from typing import Optional


class MessagingExtensionResponse(BaseModel):
    """Messaging extension response.

    :param compose_extension: The compose extension result.
    :type compose_extension: Optional["MessagingExtensionResult"]
    :param cache_info: CacheInfo for this MessagingExtensionResponse.
    :type cache_info: Optional["CacheInfo"]
    """

    compose_extension: Optional["MessagingExtensionResult"]
    cache_info: Optional["CacheInfo"]
