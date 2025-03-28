# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dotenv import load_dotenv
from aiohttp.web import Application, Request, Response, run_app

from microsoft.agents.builder import RestChannelServiceClientFactory
from microsoft.agents.builder.state import UserState
from microsoft.agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft.agents.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth
from microsoft.agents.storage import MemoryStorage

from sso_agent import SsoAgent
from config import DefaultConfig

load_dotenv()

CONFIG = DefaultConfig()
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


CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DefaultConnection())

# Create adapter.
ADAPTER = CloudAdapter(CHANNEL_CLIENT_FACTORY)

# Create the storage.
STORAGE = MemoryStorage()

# Create the user state and conversation state.
USER_STATE = UserState(STORAGE)

# Create the Agent
AGENT = SsoAgent(USER_STATE, CONFIG.CONNECTION_NAME, CONFIG.CLIENT_ID)


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
