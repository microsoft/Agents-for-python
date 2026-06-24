# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Microsoft Graph client integration for the Teams hosting layer.

Builds a :class:`msgraph.GraphServiceClient` whose requests are authenticated
with tokens obtained from the agent's configured authorization, so handlers can
call Microsoft Graph on behalf of the current turn.
"""

from typing import Any

from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.authentication import AuthenticationProvider

from msgraph import GraphServiceClient, GraphRequestAdapter

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
)


class _SDKAuthenticationProvider(AuthenticationProvider):
    """Kiota authentication provider backed by the agent's authorization.

    Acquires an access token for the current turn via
    :meth:`AgentApplication.auth.get_token` and attaches it to outgoing Graph
    requests as a bearer token.
    """

    def __init__(self, app: AgentApplication, context: TurnContext, handler_name: str):
        """Capture the context needed to resolve a token at request time.

        :param app: The agent application whose authorization issues tokens.
        :param context: The current turn context.
        :param handler_name: The auth handler name used to acquire the token.
        """
        self._app = app
        self._context = context
        self._handler_name = handler_name

    async def authenticate_request(
        self,
        request: RequestInformation,
        additional_authentication_context: dict[str, Any] | None = None,
    ) -> None:
        """Attach a bearer token to the outgoing Graph request.

        :param request: The request to authenticate.
        :param additional_authentication_context: Optional Kiota authentication
            context; unused but accepted to satisfy the provider interface.
        """
        if additional_authentication_context is None:
            additional_authentication_context = {}

        token = await self._app.auth.get_token(self._context, self._handler_name)
        if token:
            request.headers["Authorization"] = f"Bearer {token}"


def _create_graph_service_client(
    app: AgentApplication,
    context: TurnContext,
    handler_name: str | None = None,
) -> GraphServiceClient:
    """Create a Graph client authenticated for the current turn.

    :param app: The agent application whose authorization issues tokens.
    :param context: The current turn context.
    :param handler_name: Optional auth handler name used to acquire the token.
    :return: A :class:`GraphServiceClient` that authenticates each request via
        the agent's authorization.
    """
    return GraphServiceClient(
        request_adapter=GraphRequestAdapter(
            _SDKAuthenticationProvider(app, context, handler_name)
        )
    )
