# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dotenv import load_dotenv
from aiohttp.web import Application, Request, Response, run_app

from microsoft.agents.hosting import RestChannelServiceClientFactory
from microsoft.agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft.agents.hosting.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth
from openai import AsyncAzureOpenAI

from weather_agent import WeatherAgent
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

# gets the API Key from environment variable AZURE_OPENAI_API_KEY
CLIENT = AsyncAzureOpenAI(
    api_version=CONFIG.AZURE_OPENAI_API_VERSION,
    azure_endpoint=CONFIG.AZURE_OPENAI_ENDPOINT,
)

# Create the Agent
AGENT = WeatherAgent(client=CLIENT)


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
