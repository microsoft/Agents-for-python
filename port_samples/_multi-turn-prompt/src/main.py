# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Application, Request, Response, run_app

from dotenv import load_dotenv
load_dotenv(path.join(path.dirname(__file__), ".env"))

from os import path

from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    load_auth_config_from_env,
)
from microsoft.agents.hosting.core import (
    UserState,
    ConversationState,
    MemoryStorage,
    Request,
    start_agent_process,
)

from .dialog_agent import DialogAgent
from .user_profile_dialog import UserProfileDialog

auth_config = load_auth_config_from_env()
adapter = CloudAdapter(auth_config)
memory_storage = MemoryStorage()
conversation_state = ConversationState(memory_storage)
user_state = UserState(memory_storage)

dialog = UserProfileDialog(user_state)
my_bot = DialogAgent(conversation_state, user_state, dialog)

app = Application(middlewares=[jwt_authorization_middleware])

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    agent: DialogAgent = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )

APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = auth_config
APP["agent_app"] = my_bot
APP["adapter"] = adapter

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=auth_config.PORT)
    except Exception as error:
        raise error
