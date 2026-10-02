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

class _SSRFConnector(TCPConnector):

    def __init__(self, host_validator: HostValidator, *args, **kwargs):
        self._host_validator = host_validator
        super().__init__(*args, **kwargs)


    async def _resolve_host(self, host: str, port: int, traces: Sequence[Trace] | None = None) -> list[ResolveResult]:

        res = await super()._resolve_host(host, port, traces)

        for r in res:
            

        return res

class OutboundHostValidator:

    def __init__(self, enabled):

        self._connector = _SSRFConnector()

    def is_allowed(self, url: str | URL) -> bool:
        """Checks if the given URL is allowed based on the host validator.

        :param url: The URL string or URL object to check.
        :return: True if the URL is allowed, False otherwise.
        """
        return self._connector._host_validator.is_allowed(url)  # type: ignore

async def _resolve_host(connector: TCPConnector) -> list[ResolveResult]:
    return await connector._resolve_host()  # type: ignore