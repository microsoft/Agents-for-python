# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ssl
import certifi
import httpx

from microsoft_teams.common import Client, ClientOptions

_ssl_context: ssl.SSLContext | None = None


def _get_ssl_context() -> ssl.SSLContext:
    global _ssl_context

    if _ssl_context is None:
        _ssl_context = ssl.create_default_context(cafile=certifi.where())
    return _ssl_context


def _create_http_client(options: ClientOptions | None = None) -> Client:
    options = options or ClientOptions()
    client = object.__new__(Client)
    client._options = options
    client._token = options.token
    client._interceptors = list(options.interceptors or [])
    client.http = httpx.AsyncClient(
        base_url=httpx.URL(options.base_url) if options.base_url else "",
        headers=options.headers,
        timeout=options.timeout,
        verify=_get_ssl_context(),
    )
    client._update_event_hooks()
    return client
