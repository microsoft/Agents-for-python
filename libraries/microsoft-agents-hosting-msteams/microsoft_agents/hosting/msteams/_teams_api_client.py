# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Construction and caching of the Teams :class:`ApiClient` for a turn.

The client is cached on turn context services so it is built at most once per turn, and
is configured with a token factory derived from the turn's identity when one is
available.
"""

from microsoft_teams.common import ClientOptions
from microsoft_teams.api import ApiClient

from microsoft_agents.hosting.core import (
    Connections,
    TurnContext,
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

    options: ClientOptions

    if context.identity:
        provider = connection_manager.get_token_provider(
            context.identity, context.activity.service_url
        )

        async def token_factory() -> str:
            return await provider.get_access_token(
                "https://api.botframework.com",
                ["https://api.botframework.com/.default"],
            )

        options = ClientOptions(
            base_url=context.activity.service_url, headers=headers, token=token_factory
        )
    else:
        options = ClientOptions(base_url=context.activity.service_url, headers=headers)

    api_client = ApiClient(
        context.activity.service_url,
        options,
    )

    context.services.set(ApiClient, api_client)
