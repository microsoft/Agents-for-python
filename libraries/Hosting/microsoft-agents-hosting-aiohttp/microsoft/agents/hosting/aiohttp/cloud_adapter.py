# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Awaitable, Callable, Optional

from aiohttp.web import (
    Request,
    Response,
    json_response,
    WebSocketResponse,
    HTTPBadRequest,
    HTTPMethodNotAllowed,
    HTTPUnauthorized,
    HTTPUnsupportedMediaType,
)
from microsoft.agents.authentication import ClaimsIdentity
from microsoft.agents.core.models import (
    Activity,
    DeliveryModes,
    InvokeResponse,
)
from microsoft.agents.connector import ConnectorClient
from microsoft.agents.botbuilder import (
    Bot,
    ChannelServiceAdapter,
    ChannelServiceClientFactoryBase,
    MessageFactory,
    Middleware,
    TurnContext,
)

from .bot_http_adapter import BotHttpAdapter


class CloudAdapter(ChannelServiceAdapter, BotHttpAdapter):
    def __init__(
        self,
        channel_service_client_factory: ChannelServiceClientFactoryBase,
        *middlewares: Middleware,
    ):
        """
        Initializes a new instance of the CloudAdapter class.

        :param bot_framework_authentication: Optional BotFrameworkAuthentication instance
        """

        if middlewares:
            for middleware in middlewares:
                self.use(middleware)

        async def on_turn_error(context: TurnContext, error: Exception):
            error_message = f"Exception caught : {error}"

            await context.send_activity(MessageFactory.text(error_message))

            # Send a trace activity
            await context.send_trace_activity(
                "OnTurnError Trace",
                error_message,
                "https://www.botframework.com/schemas/error",
                "TurnError",
            )

        self.on_turn_error = on_turn_error

        super().__init__(channel_service_client_factory)

    async def process(self, request: Request, bot: Bot) -> Optional[Response]:
        if not request:
            raise TypeError("CloudAdapter.process: request can't be None")
        if not bot:
            raise TypeError("CloudAdapter.process: bot can't be None")

        if request.method == "POST":
            # Deserialize the incoming Activity
            if "application/json" in request.headers["Content-Type"]:
                body = await request.json()
            else:
                raise HTTPUnsupportedMediaType()

            activity: Activity = Activity.model_validate_json(body)
            # TODO: Add the ability to pass in the ClaimsIdentity
            claims_identity: ClaimsIdentity = request.get("claims_identity")

            # A POST request must contain an Activity
            if (
                not activity.type
                or not activity.conversation
                or not activity.conversation.id
            ):
                raise HTTPBadRequest

            try:
                # Process the inbound activity with the bot
                invoke_response = await self.process_activity(
                    claims_identity, activity, bot.on_turn
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
