# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import OrderedDict
from yarl import URL

def _try_create_url(url: str | URL) -> URL | None:
    """Attempts to create a URL object from the given string or URL.

    :param url: The URL string or URL object to create.
    :return: A URL object if successful, None otherwise.
    """
    try:
        return URL(url) if isinstance(url, str) else url
    except (ValueError, TypeError):
        return None

class _DNSCache:

    def __init__(self, max_size: int, ttl: float) -> None:
        self._cache = OrderedDict[tuple[str, int]]