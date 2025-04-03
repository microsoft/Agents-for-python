from pydantic import BaseModel


class CacheInfo(BaseModel):
    """A cache info object which notifies Teams how long an object should be cached for.

    :param cache_type: Type of Cache Info
    :type cache_type: str
    :param cache_duration: Duration of the Cached Info.
    :type cache_duration: int
    """

    cache_type: str
    cache_duration: int
