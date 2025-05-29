# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv

from microsoft.agents.builder import RestChannelServiceClientFactory
from microsoft.agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft.agents.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth

from empty_agent import EmptyAgent
from config import DefaultConfig

from microsoft.agents.builder import ActivityHandler, MessageFactory, TurnContext
from microsoft.agents.core.models import ChannelAccount


load_dotenv()

class EmptyAgent(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        return await turn_context.send_activity(
            MessageFactory.text(f"Echo: {turn_context.activity.text}")
        )

AUTH_PROVIDER = MsalAuth(DefaultConfig())




# Create the Agent
AGENT = EmptyAgent()


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    adapter: CloudAdapter = req.app["adapter"]
    return await adapter.process(req, AGENT)


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = CONFIG
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
