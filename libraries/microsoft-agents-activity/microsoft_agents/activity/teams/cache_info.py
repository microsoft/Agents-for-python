# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class CacheInfo(AgentsModel):
    """A cache info object which notifies Teams how long an object should be cached for.

    :param cache_type: Type of Cache Info
    :type cache_type: str | None
    :param cache_duration: Duration of the Cached Info.
    :type cache_duration: int | None
    """

    cache_type: str | None
    cache_duration: int | None
