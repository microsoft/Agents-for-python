# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Application, Request, Response, run_app

from dotenv import load_dotenv
load_dotenv(path.join(path.dirname(__file__), ".env"))

from os import path

from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft.agents.hosting.core import Agent

from .agent import (
    CardSampleAgent
)
from .card_messages import CardSampleAgent

auth_config = load_auth_config_from_env()
adapter = CloudAdapter(auth_config)
my_bot = CardSampleAgent()

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    agent: Agent = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )

APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = auth_config
APP["agent_app"] = card_sample_agent
APP["adapter"] = adapter

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=auth_config.PORT)
    except Exception as error:
        raise error
