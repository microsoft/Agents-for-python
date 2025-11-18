# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from microsoft_agents.hosting.core import Agent
from microsoft_agents.hosting.core.authorization import Connections
from microsoft_agents.hosting.core.http import (
    HttpAdapterBase,
    HttpResponse,
)
from microsoft_agents.hosting.core import ChannelServiceClientFactoryBase

from .agent_http_adapter import AgentHttpAdapter


class FastApiRequestAdapter:
    """Adapter to make FastAPI Request compatible with HttpRequestProtocol."""

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
    """CloudAdapter for FastAPI web framework."""

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
        """Process a FastAPI request.

        Args:
            request: The FastAPI request.
            agent: The agent to handle the request.

        Returns:
            FastAPI Response object.
        """
        # Adapt request to protocol
        adapted_request = FastApiRequestAdapter(request)

        # Process using base implementation
        http_response: HttpResponse = await self.process_request(adapted_request, agent)

        # Convert HttpResponse to FastAPI Response
        return self._to_fastapi_response(http_response)

    @staticmethod
    def _to_fastapi_response(http_response: HttpResponse) -> Response:
        """Convert HttpResponse to FastAPI Response."""
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
