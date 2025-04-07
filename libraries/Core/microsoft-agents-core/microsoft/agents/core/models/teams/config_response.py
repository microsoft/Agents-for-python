# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .config_response_base import ConfigResponseBase
from .cache_info import CacheInfo


class ConfigResponse(ConfigResponseBase):
    """Envelope for Config Response Payload.

    :param config: The response to the config message. Possible values: 'auth', 'task'
    :type config: object
    :param cache_info: Response cache info
    :type cache_info: CacheInfo
    """

    config: object = None
    cache_info: CacheInfo = None
