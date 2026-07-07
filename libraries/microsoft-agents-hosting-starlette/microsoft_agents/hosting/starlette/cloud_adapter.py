# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from microsoft_agents.hosting.core import Agent
from microsoft_agents.hosting.core.authorization import Connections
from microsoft_agents.hosting.core.http import (
    HttpAdapterBase,
    HttpResponse,
)
from microsoft_agents.hosting.core import ChannelServiceClientFactoryBase

from .agent_http_adapter import AgentHttpAdapter


class StarletteRequestAdapter:
    """Adapter to make a Starlette Request compatible with HttpRequestProtocol."""

    def __init__(self, request: Request):
        self._request = request

    @property
    def method(self) -> str:
        return self._request.method

    @property
    def headers(self):
        return self._request.headers

    async def json(self):
        return await self._request.json()

    def get_claims_identity(self):
        return getattr(self._request.state, "claims_identity", None)

    def get_path_param(self, name: str) -> str:
        return self._request.path_params.get(name, "")


class CloudAdapter(HttpAdapterBase, AgentHttpAdapter):
    """CloudAdapter for the Starlette web framework."""

    def __init__(
        self,
        *,
        connection_manager: Connections = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase = None,
    ):
        """
        Initializes a new instance of the CloudAdapter class.

        :param connection_manager: Optional connection manager for OAuth.
        :param channel_service_client_factory: The factory to use to create the channel service client.
        """
        super().__init__(
            connection_manager=connection_manager,
            channel_service_client_factory=channel_service_client_factory,
        )

    async def process(self, request: Request, agent: Agent) -> Optional[Response]:
        """Process a Starlette request.

        Args:
            request: The Starlette request.
            agent: The agent to handle the request.

        Returns:
            Starlette Response object.
        """
        # Adapt request to protocol
        adapted_request = StarletteRequestAdapter(request)

        # Process using base implementation
        http_response: HttpResponse = await self.process_request(adapted_request, agent)

        # Convert HttpResponse to Starlette Response
        return self._to_starlette_response(http_response)

    @staticmethod
    def _to_starlette_response(http_response: HttpResponse) -> Response:
        """Convert HttpResponse to a Starlette Response."""
        if http_response.body is not None:
            return JSONResponse(
                content=http_response.body,
                status_code=http_response.status_code,
                headers=http_response.headers,
            )
        return Response(
            status_code=http_response.status_code,
            headers=http_response.headers,
        )
