# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_teams.common import ClientOptions
from microsoft_teams.api import ApiClient

from microsoft_agents.hosting.core import (
    Connections,
    TurnContext,
)

_TEAMS_API_CLIENT_KEY = "TeamsApiClient"


def get_cached_teams_api_client(context: TurnContext) -> ApiClient:
    client = context.turn_state.get(_TEAMS_API_CLIENT_KEY)
    if isinstance(client, ApiClient):
        return client
    raise ValueError("Unable to retrieve Teams API client.")


async def get_teams_api_client(
    context: TurnContext,
    connections: Connections | None = None,
) -> ApiClient:

    state = context.turn_state.get(_TEAMS_API_CLIENT_KEY)
    if isinstance(state, ApiClient):
        return state

    if not connections:
        raise ValueError("Unable to retrieve Teams API client.")

    token: str | None = None
    if context.identity:
        assert context.identity is not None
        provider = connections.get_token_provider(
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

    return api_client
