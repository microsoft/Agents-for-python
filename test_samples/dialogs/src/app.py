# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import path, environ

from aiohttp import web
from aiohttp.web import Request, Response
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.core import (
    ConversationState,
    MemoryStorage,
    UserState,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.activity import load_configuration_from_env
from dotenv import load_dotenv

from .user_profile_dialog import UserProfileDialog
from .agent import DialogAgent

load_dotenv(path.join(path.dirname(__file__), ".env"))
agents_sdk_config = load_configuration_from_env(dict(environ))

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)

CONVERSATION_STATE = ConversationState(STORAGE)
USER_STATE = UserState(STORAGE)

DIALOG = UserProfileDialog(USER_STATE)
AGENT = DialogAgent(CONVERSATION_STATE, USER_STATE, DIALOG)

# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:
    return await ADAPTER.process(req, AGENT)


APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error