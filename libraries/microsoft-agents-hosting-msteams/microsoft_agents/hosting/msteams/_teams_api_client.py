# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Construction and caching of the Teams :class:`ApiClient` for a turn.

The client is cached on turn context services so it is built at most once per turn, and
is configured with a token factory derived from the turn's identity when one is
available.
"""

import ssl
import certifi

from typing import Callable, Awaitable

import httpx

from microsoft_teams.common import Client, ClientOptions
from microsoft_teams.api import ApiClient

from microsoft_agents.hosting.core import (
    Connections,
    TurnContext,
)

_ssl_context: ssl.SSLContext | None = None


def _get_ssl_context() -> ssl.SSLContext:
    """Get or create the SSL context for verifying HTTPS requests.

    httpx by default creates a new SSL context for each new client instance. This can be
    inefficient. For example, at the time of writing this, without caching the SSL context,
    the hosting_msteams unit tests took 32 seconds to complete. With caching, the total
    time for the unit tests dropped to 7 seconds. For an agent with lots of traffic,
    caching the SSL context may significantly improve performance and avoid extra io operations.
    """
    global _ssl_context

    if _ssl_context is None:
        _ssl_context = ssl.create_default_context(cafile=certifi.where())
    return _ssl_context


def _client(
    base_url: str,
    headers: dict,
    token_factory: Callable[[], Awaitable[str]] | None = None,
) -> Client:
    """
    Create a new Client instance configured with the given base URL, headers, and token factory.

    :param base_url: The base URL for the client.
    :param headers: The headers to include in the client requests.
    :param token_factory: A callable that returns an access token asynchronously, or None if no token is required.
    :return: A configured Client instance.
    """

    options = ClientOptions(
        base_url=base_url,
        headers=headers,
        token=token_factory,
    )

    return Client(
        options,
        _http=httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=options.timeout,
            verify=_get_ssl_context(),
        ),
    )


def _get_teams_api_client(context: TurnContext) -> ApiClient:
    """
    Get the cached Teams API client from the context.

    :param context: The turn context.
    :return: The cached Teams API client.
    :raises ValueError: If the Teams API client is not found.
    """
    api_client = context.services.get(ApiClient)
    if isinstance(api_client, ApiClient):
        return api_client
    raise ValueError("Unable to retrieve Teams API client.")


def _set_teams_api_client(
    context: TurnContext, connection_manager: Connections
) -> None:
    """
    Set the Teams API client in the context if it is not already set.

    :param context: The turn context.
    :param connection_manager: The connection manager.
    """

    if context.services.has(ApiClient):
        return

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    token_factory: Callable[[], Awaitable[str]] | None = None

    if context.identity:
        provider = connection_manager.get_token_provider(
            context.identity, context.activity.service_url
        )

        async def _token_factory() -> str:
            return await provider.get_access_token(
                "https://api.botframework.com",
                ["https://api.botframework.com/.default"],
            )

        token_factory = _token_factory

    api_client = ApiClient(
        context.activity.service_url,
        options=_client(
            base_url=context.activity.service_url,
            headers=headers,
            token_factory=token_factory,
        ),
    )

    context.services.set(ApiClient, api_client)
