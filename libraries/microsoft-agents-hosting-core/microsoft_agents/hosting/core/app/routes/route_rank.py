from enum import IntEnum

MAX_RANK = 2**32 - 1  # Python ints don't have a max value, LOL


class RouteRank(IntEnum):
    """Defines the rank of a route. Lower values indicate higher priority."""

    FIRST = 0
    DEFAULT = MAX_RANK // 2
    LAST = MAX_RANK
