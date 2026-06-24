# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.authentication import AuthenticationProvider

from msgraph import GraphServiceClient, GraphRequestAdapter

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
)


class _SDKAuthenticationProvider(AuthenticationProvider):

    def __init__(self, app: AgentApplication, context: TurnContext, handler_name: str):
        self._app = app
        self._context = context
        self._handler_name = handler_name

    async def authenticate_request(
        self,
        request: RequestInformation,
        additional_authentication_context: dict[str, Any] | None = None,
    ) -> None:
        """Authenticates the application request

        Args:
            request (RequestInformation): The request to authenticate
            additional_authentication_context (dict):
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
    return GraphServiceClient(
        request_adapter=GraphRequestAdapter(
            _SDKAuthenticationProvider(app, context, handler_name)
        )
    )
