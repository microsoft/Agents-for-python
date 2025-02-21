# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Application, Request, Response, run_app

from microsoft.agents.botbuilder import RestChannelServiceClientFactory
from microsoft.agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware, channel_service_route_table
from microsoft.agents.authentication import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authorization.msal import MsalAuth
from microsoft.agents.client import ConfigurationChannelHost, ConversationIdFactory, HttpBotChannelFactory
from microsoft.agents.storage import MemoryStorage

from bot1 import Bot1
from config import DefaultConfig

AUTH_PROVIDER = MsalAuth(DefaultConfig())


class DefaultConnection(Connections):
    def get_default_connection(self) -> AccessTokenProviderBase:
        pass

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        return AUTH_PROVIDER

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        pass

DEFAULT_CONNECTION = DefaultConnection()
CONFIG = DefaultConfig()
CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DEFAULT_CONNECTION)

BOT_CHANNEL_FACTORY = HttpBotChannelFactory()
CHANNEL_HOST = ConfigurationChannelHost(BOT_CHANNEL_FACTORY, DEFAULT_CONNECTION, CONFIG, "HttpBotClient")
STORAGE = MemoryStorage()
CONVERSATION_ID_FACTORY = ConversationIdFactory(STORAGE)

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
ADAPTER = CloudAdapter(CHANNEL_CLIENT_FACTORY)

# Create the Bot
BOT = Bot1(adapter=ADAPTER, channel_host=CHANNEL_HOST, )


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    adapter: CloudAdapter = req.app["adapter"]
    return await adapter.process(req, BOT)


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP.router.add_routes(channel_service_route_table(BOT, "/api/botresponse"))
APP["bot_configuration"] = CONFIG
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
