# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_teams.common import ClientOptions
from microsoft_teams.api import ApiClient

from microsoft_agents.hosting.core import (
    Connections,
    TurnContext,
)

_TEAMS_API_CLIENT_KEY = "TeamsApiClient"


def get_teams_api_client(context: TurnContext) -> ApiClient:
    """
    Get the cached Teams API client from the context.

    :param context: The turn context.
    :return: The cached Teams API client.
    :raises ValueError: If the Teams API client is not found.
    """
    api_client = context.turn_state.get(_TEAMS_API_CLIENT_KEY)
    if isinstance(api_client, ApiClient):
        return api_client
    raise ValueError("Unable to retrieve Teams API client.")


def set_teams_api_client(context: TurnContext, connection_manager: Connections) -> None:
    """
    Set the Teams API client in the context if it is not already set.

    :param context: The turn context.
    :param connection_manager: The connection manager.
    """

    if _TEAMS_API_CLIENT_KEY in context.turn_state:
        return

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    options: ClientOptions

    if context.identity:
        assert context.identity is not None
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

    context.turn_state[_TEAMS_API_CLIENT_KEY] = api_client
