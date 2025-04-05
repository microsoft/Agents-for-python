# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import Optional


class CacheInfo(BaseModel):
    """A cache info object which notifies Teams how long an object should be cached for.

    :param cache_type: Type of Cache Info
    :type cache_type: Optional[str]
    :param cache_duration: Duration of the Cached Info.
    :type cache_duration: Optional[int]
    """

    cache_type: Optional[str]
    cache_duration: Optional[int]
