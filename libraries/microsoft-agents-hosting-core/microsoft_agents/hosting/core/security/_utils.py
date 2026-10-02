# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from aiohttp import TCPConnector
from aiohttp.abc import ResolveResult

import ipaddress

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


def _normalize_host(host: str) -> str | None:
    """Normalizes the given host string.

    :param host: The host string to normalize.
    :return: The normalized host string.
    """
    if not host:
        return None

    host = host.strip().casefold()

    if host.startswith("*."):
        host = host[2:]

    url_obj = _try_create_url(host)
    if url_obj and url_obj.host:
        host = url_obj.host
    else:
        slash = host.find("/")
        if slash >= 0:
            host = host[:slash]

        colon = host.find(":")
        if colon >= 0:
            host = host[:colon]

    return host if host else None
