# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Base HTTP adapter with shared processing logic."""

from abc import ABC
from http import HTTPStatus
from traceback import format_exc

import logging

from microsoft_agents.activity import Activity, DeliveryModes
from microsoft_agents.hosting.core.telemetry.adapter import spans

from .agent import Agent
from .authorization.claims_identity import ClaimsIdentity
from .authorization.connections import Connections
from .channel_service_adapter import ChannelServiceAdapter
from .channel_service_client_factory_base import ChannelServiceClientFactoryBase
from .http._http_request_protocol import HttpRequestProtocol
from .http._http_response import HttpResponse, HttpResponseFactory
from .message_factory import MessageFactory
from .rest_channel_service_client_factory import RestChannelServiceClientFactory
from .turn_context import TurnContext
from .outbound_host_validator import OutboundHostValidator, _try_create_url

logger = logging.getLogger(__name__)


class HttpAdapterBase(ChannelServiceAdapter, ABC):
    """Base adapter for HTTP-based agent hosting with shared processing logic.

    This class contains all the common logic for processing HTTP requests
    and can be subclassed by framework-specific adapters (aiohttp, FastAPI, etc).
    """

    def __init__(
        self,
        *,
        connection_manager: Connections | None = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase | None = None,
        channel_service_client_factory_options: dict | None = None,
        host_validator: OutboundHostValidator | None = None,
    ):
        """Initialize the HTTP adapter.

        :param connection_manager: Optional connection manager for OAuth.
        :param channel_service_client_factory: Factory for creating channel service clients.
        :param channel_service_client_factory_options: Optional dictionary of options to pass to the channel service client factory
            This is only used if channel_service_client_factory is not provided and connection_manager is provided.
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

        factory: ChannelServiceClientFactoryBase

        if channel_service_client_factory:
            factory = channel_service_client_factory
        else:
            if not connection_manager:
                raise ValueError(
                    "HttpAdapterBase.__init__: Either channel_service_client_factory or connection_manager must be provided."
                )
            factory = RestChannelServiceClientFactory(
                connection_manager,
                **(channel_service_client_factory_options or {}),
            )
        self._host_validator = host_validator or OutboundHostValidator()

        super().__init__(factory)

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

    def _validate_service_url(
        self, claims_identity: ClaimsIdentity, activity: Activity
    ) -> bool:
        """Validate the service URL against the claims identity.

        Args:
            claims_identity: The claims identity to validate against.
            activity: The activity containing the service URL to validate.

        Returns:
            True if the service URL is valid, False otherwise.
        """

        if (
            self._host_validator.enabled
            and activity.service_url
            and not self._host_validator.is_allowed(activity.service_url)
        ):
            logger.warning(
                "Service URL %s is not allowed by the host validator.",
                activity.service_url,
            )
            return False

        if not claims_identity:
            return True

        claims_service_url = claims_identity.get_claim_value("serviceurl")
        if activity.service_url and claims_service_url:
            claim_url = _try_create_url(claims_service_url)
            activity_url = _try_create_url(activity.service_url)
            claim_url_host = (claim_url.host or "") if claim_url else ""
            activity_url_host = (activity_url.host or "") if activity_url else ""
            if (
                not claim_url
                or not activity_url
                or claim_url_host.casefold() != activity_url_host.casefold()
            ):
                if self._host_validator and self._host_validator.enabled:
                    logger.warning(
                        "Service URL host mismatch: %s vs %s",
                        claim_url_host,
                        activity_url_host,
                    )
                    return False
                else:
                    logger.warning(
                        "Service URL host mismatch (host validator disabled): %s vs %s",
                        claim_url_host,
                        activity_url_host,
                    )

        return True
