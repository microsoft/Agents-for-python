# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv

from microsoft.agents.hosting.core import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
    ConfigurationChannelHost,
    ConversationIdFactory,
    HttpAgentChannelFactory,
    MemoryStorage,
    RestChannelServiceClientFactory,
)
from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    channel_service_route_table,
)
from microsoft.agents.authentication.msal import MsalAuth

from agent1 import Agent1
from config import DefaultConfig

load_dotenv()

AUTH_PROVIDER = MsalAuth(DefaultConfig())


class DefaultConnection(Connections):
    def get_default_connection(self) -> AccessTokenProviderBase:
        pass

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        # This is the provider used for ABS
        return AUTH_PROVIDER

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        # In this case we are using the same settings for both ABS and Channel
        # This is the provider used for Channel
        return AUTH_PROVIDER


DEFAULT_CONNECTION = DefaultConnection()
CONFIG = DefaultConfig()
CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DEFAULT_CONNECTION)

AGENT_CHANNEL_FACTORY = HttpAgentChannelFactory()
CHANNEL_HOST = ConfigurationChannelHost(
    AGENT_CHANNEL_FACTORY, DEFAULT_CONNECTION, CONFIG, "HttpAgentClient"
)
STORAGE = MemoryStorage()
CONVERSATION_ID_FACTORY = ConversationIdFactory(STORAGE)

# Create adapter.
ADAPTER = CloudAdapter(CHANNEL_CLIENT_FACTORY)

# Create the Agent
AGENT = Agent1(
    adapter=ADAPTER,
    channel_host=CHANNEL_HOST,
    conversation_id_factory=CONVERSATION_ID_FACTORY,
)


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    adapter: CloudAdapter = req.app["adapter"]
    return await adapter.process(req, AGENT)


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP.router.add_routes(channel_service_route_table(AGENT, "/api/botresponse"))
APP["agent_configuration"] = CONFIG
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
