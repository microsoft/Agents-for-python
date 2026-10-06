# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

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


def _normalize_ip_address(address: str) -> str | None:
    """Check for potential ip address and normalize

    :param address: The IP address string to normalize.
    :return: The normalized IP address string if valid, None otherwise.
    """

    right_bracket = -1
    if address.startswith("["):
        for i, c in enumerate(address[::-1]):
            if c == "]":
                right_bracket = len(address) - i - 1
                break

    if right_bracket >= 0:
        address = address[1:right_bracket]

    try:
        return str(ipaddress.ip_address(address))
    except ValueError:
        return None


def _normalize_host(host: str) -> str | None:
    """Normalizes the given host string.

    :param host: The host string to normalize.
    :return: The normalized host string.
    """
    if not host:
        return None

    host = host.strip().casefold()

    ip_address = _normalize_ip_address(host)
    if ip_address is not None:
        return ip_address

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
