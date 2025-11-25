# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Base HTTP adapter with shared processing logic."""

from abc import ABC
from traceback import format_exc

from microsoft_agents.activity import Activity, DeliveryModes
from microsoft_agents.hosting.core.authorization import ClaimsIdentity, Connections
from microsoft_agents.hosting.core import (
    Agent,
    ChannelServiceAdapter,
    ChannelServiceClientFactoryBase,
    MessageFactory,
    RestChannelServiceClientFactory,
    TurnContext,
)

from ._http_request_protocol import HttpRequestProtocol
from ._http_response import HttpResponse, HttpResponseFactory


class HttpAdapterBase(ChannelServiceAdapter, ABC):
    """Base adapter for HTTP-based agent hosting with shared processing logic.

    This class contains all the common logic for processing HTTP requests
    and can be subclassed by framework-specific adapters (aiohttp, FastAPI, etc).
    """

    def __init__(
        self,
        *,
        connection_manager: Connections = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase = None,
    ):
        """Initialize the HTTP adapter.

        Args:
            connection_manager: Optional connection manager for OAuth.
            channel_service_client_factory: Factory for creating channel service clients.
        """

        async def on_turn_error(context: TurnContext, error: Exception):
            error_message = f"Exception caught : {error}"
            print(format_exc())

            await context.send_activity(MessageFactory.text(error_message))

            # Send a trace activity
            await context.send_trace_activity(
                "OnTurnError Trace",
                error_message,
                "https://www.botframework.com/schemas/error",
                "TurnError",
            )

        self.on_turn_error = on_turn_error

        channel_service_client_factory = (
            channel_service_client_factory
            or RestChannelServiceClientFactory(connection_manager)
        )

        super().__init__(channel_service_client_factory)

    async def process_request(
        self, request: HttpRequestProtocol, agent: Agent
    ) -> HttpResponse:
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

        if request.method != "POST":
            return HttpResponseFactory.method_not_allowed()

        # Deserialize the incoming Activity
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return HttpResponseFactory.unsupported_media_type()

        try:
            body = await request.json()
        except Exception:
            return HttpResponseFactory.bad_request("Invalid JSON")

        activity: Activity = Activity.model_validate(body)

        # Get claims identity (default to anonymous if not set by middleware)
        claims_identity: ClaimsIdentity = (
            request.get_claims_identity() or ClaimsIdentity({}, False)
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
                # Invoke and ExpectReplies cannot be performed async
                return HttpResponseFactory.json(
                    invoke_response.body, invoke_response.status
                )

            return HttpResponseFactory.accepted()

        except PermissionError:
            return HttpResponseFactory.unauthorized()
