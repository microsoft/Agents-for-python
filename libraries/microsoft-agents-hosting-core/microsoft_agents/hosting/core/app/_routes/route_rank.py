# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import IntEnum

_MAX_RANK = 2**16 - 1  # 65,535


class RouteRank(IntEnum):
    """Defines the rank of a route. Lower values indicate higher priority."""

    FIRST = 0
    DEFAULT = _MAX_RANK // 2
    LAST = _MAX_RANK
