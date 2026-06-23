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

async def _set_teams_api_client(
        context: TurnContext,
        connection_manager: Connections
    ) -> None:
    """
    Set the Teams API client in the context.

    :param context: The turn context.
    :param connection_manager: The connection manager.
    """
    token: str | None = None
    if context.identity:
        assert context.identity is not None
        provider = connection_manager.get_token_provider(
            context.identity, context.activity.service_url
        )
        token = await provider.get_access_token(
            "https://api.botframework.com", ["https://api.botframework.com/.default"]
        )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    options = ClientOptions(
        base_url=context.activity.service_url, headers=headers, token=token
    )

    api_client = ApiClient(
        context.activity.service_url,
        options,
    )

    context.turn_state[_TEAMS_API_CLIENT_KEY] = api_client