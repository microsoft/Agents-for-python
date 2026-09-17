# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from microsoft_agents.hosting.core import Agent, HttpAdapterBase
from microsoft_agents.hosting.core.authorization import Connections
from microsoft_agents.hosting.core.http import (
    HttpResponse,
)
from microsoft_agents.hosting.core import (
    ChannelServiceClientFactoryBase,
    OutboundHostValidator,
)

from .agent_http_adapter import AgentHttpAdapter
from ._fastapi_request_adapter import FastApiRequestAdapter


class CloudAdapter(HttpAdapterBase, AgentHttpAdapter):
    """CloudAdapter for FastAPI web framework."""

    def __init__(
        self,
        *,
        connection_manager: Connections | None = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase | None = None,
        channel_service_client_factory_options: dict | None = None,
        host_validator: OutboundHostValidator | None = None,
    ):
        """
        Initializes a new instance of the CloudAdapter class.

        :param connection_manager: Optional connection manager for OAuth.
        :param channel_service_client_factory: Factory for creating channel service clients.
        :param channel_service_client_factory_options: Optional dictionary of options to pass to the channel service client factory
            This is only used if channel_service_client_factory is not provided and connection_manager is provided.
        """
        super().__init__(
            connection_manager=connection_manager,
            channel_service_client_factory=channel_service_client_factory,
            channel_service_client_factory_options=channel_service_client_factory_options,
            host_validator=host_validator,
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

    async def process_request(self, request: HttpRequestProtocol, agent: Agent) -> HttpResponse:
        """Process an incoming HTTP request.

        Args:
            request: The HTTP request to process.
            agent: The agent to handle the request.

        Returns:
            HttpResponse with the result.

        Raises:
            TypeError: If request or agent is None.
        """
        if not request:
            raise TypeError("HttpAdapterBase.process_request: request can't be None")
        if not agent:
            raise TypeError("HttpAdapterBase.process_request: agent can't be None")

        with spans.AdapterProcess() as span:

            if request.method != "POST":
                return HttpResponseFactory.method_not_allowed()

            try:
                body = await request.json()
            except Exception:
                return HttpResponseFactory.bad_request(
                    "Invalid JSON or unsupported Content-Type"
                )

            activity: Activity = Activity.model_validate(body)
            span.share(activity=activity)

            # Get claims identity (default to anonymous if not set by middleware)
            claims_identity: ClaimsIdentity = (
                request.get_claims_identity() or ClaimsIdentity()
            )

            # Validate required activity fields
            if (
                not activity.type
                or not activity.conversation
                or not activity.conversation.id
            ):
                return HttpResponseFactory.bad_request(
                    "Activity must have type and conversation.id"
                )

            if not self._validate_service_url(claims_identity, activity):
                return HttpResponseFactory.unauthorized(
                    "Service URL is not allowed by the host validator."
                )

            try:
                # Process the inbound activity with the agent
                invoke_response = await self.process_activity(
                    claims_identity, activity, agent.on_turn
                )

                # Check if we need to return a synchronous response
                if (
                    activity.type == "invoke"
                    or activity.delivery_mode == DeliveryModes.expect_replies
                ):
                    with spans.AdapterWriteResponse(activity):
                        # Invoke and ExpectReplies cannot be performed async
                        invoke_response_status = (
                            invoke_response.status if invoke_response else None
                        )
                        return HttpResponseFactory.json(
                            invoke_response.body if invoke_response else None,
                            invoke_response_status or HTTPStatus.NOT_IMPLEMENTED,
                        )

                return HttpResponseFactory.accepted()

            except PermissionError:
                return HttpResponseFactory.unauthorized()

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
