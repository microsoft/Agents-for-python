# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Microsoft Graph client integration for the Teams hosting layer.

Builds a :class:`msgraph.GraphServiceClient` whose requests are authenticated
with tokens obtained from the agent's configured authorization, so handlers can
call Microsoft Graph on behalf of the current turn.
"""

from typing import Any
from urllib.parse import urlparse

from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.authentication import AuthenticationProvider

from msgraph import GraphServiceClient, GraphRequestAdapter

from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    TurnContext,
    AccessTokenProviderBase,
)

_DEFAULT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class _SDKUserAuthenticationProvider(AuthenticationProvider):
    """Kiota authentication provider backed by the agent's authorization.

    Acquires an access token for the current turn via
    :meth:`AgentApplication.auth.get_token` and attaches it to outgoing Graph
    requests as a bearer token.
    """

    def __init__(
        self,
        auth: Authorization,
        context: TurnContext,
        handler_name: str | None = None,
    ):
        """Capture the context needed to resolve a token at request time.

        :param auth: The agent application's authorization.
        :param context: The current turn context.
        :param handler_name: Optional name of the handler to use for authentication.
        """
        self._auth = auth
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

        token_response = await self._auth.get_token(self._context, self._handler_name)
        if token_response and token_response.token:
            request.headers.add("Authorization", f"Bearer {token_response.token}")


class _SDKAuthenticationProvider(AuthenticationProvider):

    def __init__(
        self,
        token_provider: AccessTokenProviderBase,
        resource_url: str,
        scopes: list[str],
    ):
        """Capture the context needed to resolve a token at request time.

        :param token_provider: The access token provider for the agent application.
        :param resource_url: The resource URL for which to acquire the token.
        :param scopes: The scopes for which to acquire the token.
        """
        self._token_provider = token_provider
        self._resource_url = resource_url
        self._scopes = scopes

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

        token = await self._token_provider.get_access_token(
            self._resource_url, self._scopes
        )
        if token:
            request.headers.add("Authorization", f"Bearer {token}")


def _create_user_graph_service_client(
    app: AgentApplication,
    context: TurnContext,
    handler_name: str | None = None,
    graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
) -> GraphServiceClient:
    """Create a Graph client authenticated for the current turn.

    :param app: The agent application whose authorization issues tokens.
    :param context: The current turn context.
    :param handler_name: Optional auth handler name used to acquire the token.
    :return: A :class:`GraphServiceClient` that authenticates each request via
        the agent's authorization.
    """
    adapter = GraphRequestAdapter(
        _SDKUserAuthenticationProvider(app.auth, context, handler_name)
    )
    adapter.base_url = graph_base_url.rstrip("/") + "/"
    return GraphServiceClient(request_adapter=adapter)


def _create_app_graph_service_client(
    token_provider: AccessTokenProviderBase,
    graph_base_url: str,
) -> GraphServiceClient:
    """Create a Graph client authenticated for the agent application.

    :param token_provider: The access token provider for the agent application.
    :param graph_base_url: The base URL for the Graph API.
    :return: A :class:`GraphServiceClient` that authenticates each request via
        the token provider.
    """
    url_parsed = urlparse(graph_base_url)
    resource_url = f"{url_parsed.scheme}://{url_parsed.netloc}"
    scopes = [f"{resource_url}/.default"]
    request_adapter = GraphRequestAdapter(
        _SDKAuthenticationProvider(token_provider, resource_url, scopes)
    )
    request_adapter.base_url = graph_base_url.rstrip("/") + "/"
    return GraphServiceClient(request_adapter=request_adapter)


def _common_get_app_graph_client(
    app: AgentApplication,
    context: TurnContext,
    graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
) -> GraphServiceClient:
    """Get a Graph client authenticated for the agent application.

    :param app: The agent application whose authorization issues tokens.
    :param context: The current turn context.
    :param graph_base_url: The base URL for the Graph API.
    :return: A :class:`GraphServiceClient` that authenticates each request via
        the agent's authorization.
    """
    if not context.identity:
        raise ValueError("TurnContext.identity is required to get a Graph client.")
    token_provider = app.connection_manager.get_token_provider(
        context.identity, context.activity.service_url
    )
    return _create_app_graph_service_client(token_provider, graph_base_url)


def _common_get_app_graph_client_for_connection(
    app: AgentApplication,
    connection_name: str | None = None,
    graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
) -> GraphServiceClient:
    """Get a Graph client authenticated for the agent application.

    :param app: The agent application whose authorization issues tokens.
    :param connection_name: Optional connection name to select a specific token provider.
    :param graph_base_url: The base URL for the Graph API.
    :return: A :class:`GraphServiceClient` that authenticates each request via
        the token provider from the connection.
    """
    token_provider: AccessTokenProviderBase
    if not connection_name:
        token_provider = app.connection_manager.get_default_connection()
    else:
        token_provider = app.connection_manager.get_connection(connection_name)

    return _create_app_graph_service_client(token_provider, graph_base_url)
