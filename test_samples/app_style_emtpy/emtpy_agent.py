# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
import sys
import traceback
from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv

from os import environ
from microsoft.agents.authentication.msal import AuthTypes, MsalAuthConfiguration
from microsoft.agents.builder.app import AgentApplication, TurnState
from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft.agents.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth

from microsoft.agents.builder import RestChannelServiceClientFactory, TurnContext
from microsoft.agents.storage import MemoryStorage

load_dotenv()


class DefaultConfig(MsalAuthConfiguration):
    """Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get("TENANT_ID")
        self.CLIENT_ID = "" or environ.get("CLIENT_ID")
        self.CLIENT_SECRET = "" or environ.get("CLIENT_SECRET")
        self.PORT = 3978


CONFIG = DefaultConfig()
AUTH_PROVIDER = MsalAuth(CONFIG)


class DefaultConnection(Connections):
    def get_default_connection(self) -> AccessTokenProviderBase:
        pass

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        return AUTH_PROVIDER

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        pass


CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DefaultConnection())

# Create adapter.
ADAPTER = CloudAdapter(CHANNEL_CLIENT_FACTORY)

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(),
    adapter=ADAPTER,
)


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the empty agent! "
        "This agent is designed to be a starting point for your own agent development."
    )
    return True


@AGENT_APP.message(re.compile(r"^hello$"))
async def on_hello(context: TurnContext, _state: TurnState):
    await context.send_activity("Hello! How can I assist you today?")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(f"you said: {context.activity.text}")


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    agent: AgentApplication = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = CONFIG
APP["agent_app"] = AGENT_APP
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
