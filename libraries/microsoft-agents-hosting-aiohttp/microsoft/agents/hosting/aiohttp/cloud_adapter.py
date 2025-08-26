# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from traceback import format_exc
from typing import Optional

from aiohttp.web import (
    Request,
    Response,
    json_response,
    HTTPBadRequest,
    HTTPMethodNotAllowed,
    HTTPUnauthorized,
    HTTPUnsupportedMediaType,
)
from microsoft.agents.hosting.core.authorization import (
    ClaimsIdentity,
    Connections,
)
from microsoft.agents.activity import (
    Activity,
    DeliveryModes,
)
from microsoft.agents.hosting.core import (
    Agent,
    ChannelServiceAdapter,
    ChannelServiceClientFactoryBase,
    MessageFactory,
    RestChannelServiceClientFactory,
    TurnContext,
)

from .agent_http_adapter import AgentHttpAdapter


class CloudAdapter(ChannelServiceAdapter, AgentHttpAdapter):
    def __init__(
        self,
        *,
        connection_manager: Connections = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase = None,
    ):
        """
        Initializes a new instance of the CloudAdapter class.

        :param channel_service_client_factory: The factory to use to create the channel service client.
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

    async def process(self, request: Request, agent: Agent) -> Optional[Response]:
        if not request:
            raise TypeError("CloudAdapter.process: request can't be None")
        if not agent:
            raise TypeError("CloudAdapter.process: agent can't be None")

        if request.method == "POST":
            # Deserialize the incoming Activity
            if "application/json" in request.headers["Content-Type"]:
                body = await request.json()
            else:
                raise HTTPUnsupportedMediaType()

            activity: Activity = Activity.model_validate(body)
            claims_identity: ClaimsIdentity = request.get("claims_identity")

            # A POST request must contain an Activity
            if (
                not activity.type
                or not activity.conversation
                or not activity.conversation.id
            ):
                raise HTTPBadRequest

            try:
                # Process the inbound activity with the agent
                invoke_response = await self.process_activity(
                    claims_identity, activity, agent.on_turn
                )

                if (
                    activity.type == "invoke"
                    or activity.delivery_mode == DeliveryModes.expect_replies
                ):
                    # Invoke and ExpectReplies cannot be performed async, the response must be written before the calling thread is released.
                    return json_response(
                        data=invoke_response.body, status=invoke_response.status
                    )

                return Response(status=202)
            except PermissionError:
                raise HTTPUnauthorized
        else:
            raise HTTPMethodNotAllowed
