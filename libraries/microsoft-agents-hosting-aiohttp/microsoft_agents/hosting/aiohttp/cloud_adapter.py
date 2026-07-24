# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from aiohttp.web import Request, Response, json_response

from microsoft_agents.hosting.core import Agent
from microsoft_agents.hosting.core.authorization import Connections
from microsoft_agents.hosting.core.http import (
    HttpAdapterBase,
    HttpResponse,
)
from microsoft_agents.hosting.core import ChannelServiceClientFactoryBase

from .agent_http_adapter import AgentHttpAdapter
from ._aiohttp_request_adapter import AiohttpRequestAdapter


class CloudAdapter(HttpAdapterBase, AgentHttpAdapter):
    """CloudAdapter for aiohttp web framework."""

    def __init__(
        self,
        *,
        connection_manager: Connections | None = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase | None = None,
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
        """Process an aiohttp request.

        Args:
            request: The aiohttp request.
            agent: The agent to handle the request.

        Returns:
            aiohttp Response object.
        """

        # Adapt request to protocol
        adapted_request = AiohttpRequestAdapter(request)

        # Process using base implementation
        http_response: HttpResponse = await self.process_request(adapted_request, agent)

        # Convert HttpResponse to aiohttp Response
        return self._to_aiohttp_response(http_response)

    @staticmethod
    def _to_aiohttp_response(http_response: HttpResponse) -> Response:
        """Convert HttpResponse to aiohttp Response."""
        if http_response.body is not None:
            return json_response(
                data=http_response.body,
                status=http_response.status_code,
                headers=http_response.headers,
            )
        return Response(
            status=http_response.status_code,
            headers=http_response.headers,
        )
