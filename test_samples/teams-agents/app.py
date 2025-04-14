# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pathlib
from dotenv import load_dotenv
from aiohttp.web import Application, Request, Response, run_app, static

from microsoft.agents.builder import RestChannelServiceClientFactory
from microsoft.agents.builder.state import UserState
from microsoft.agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft.agents.hosting.teams import TeamsCloudAdapter
from microsoft.agents.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth
from microsoft.agents.storage import MemoryStorage

from teams_handler import TeamsHandler
from teams_sso import TeamsSso
from teams_multi_feature import TeamsMultiFeature
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
        return AUTH_PROVIDER


CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DefaultConnection())

# Create adapter.
ADAPTER = TeamsCloudAdapter(CHANNEL_CLIENT_FACTORY)

# Create the storage and user state (for SSO agent)
STORAGE = MemoryStorage()
USER_STATE = UserState(STORAGE)

def create_agent(agent_type: str):
    """
    Create the appropriate agent based on configuration.
    """
    if agent_type == "TeamsSso":
        return TeamsSso(USER_STATE, CONFIG.CONNECTION_NAME, CONFIG.CLIENT_ID)
    elif agent_type == "TeamsMultiFeature":
        return TeamsMultiFeature()
    else:  # Default to TeamsHandler
        return TeamsHandler()

# Create the agent based on configuration
AGENT = create_agent(CONFIG.AGENT_TYPE)


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    adapter: CloudAdapter = req.app["adapter"]
    return await adapter.process(req, AGENT)


# Return the YouTube page
async def youtube(req: Request) -> Response:
    return await render_page(req, "youtube.html")


# Return the custom form page
async def custom_form(req: Request) -> Response:
    return await render_page(req, "customForm.html")


# Handle form submission
async def handle_form(req: Request) -> Response:
    print("Data is being sent from the form")
    return Response(text="Form data received")


async def render_page(req: Request, page_name: str) -> Response:
    pages_path = pathlib.Path(__file__).parent / "pages"
    if not pages_path.exists():
        pages_path.mkdir()
    
    page_file = pages_path / page_name
    
    if page_file.exists():
        with open(page_file, "r") as file:
            content = file.read()
            return Response(text=content, content_type="text/html")
    else:
        return Response(text="Page not found", status=404)


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/Youtube", youtube)
APP.router.add_get("/CustomForm", custom_form)
APP.router.add_post("/CustomForm", handle_form)

# Add static file handling for CSS, JS, etc.
static_path = pathlib.Path(__file__).parent / "public"
if static_path.exists():
    APP.router.add_static('/public', static_path)

APP["agent_configuration"] = CONFIG
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        port = CONFIG.PORT
        print(f"\nServer listening on port {port} for appId {CONFIG.CLIENT_ID}")
        run_app(APP, host="localhost", port=port)
    except Exception as error:
        raise error