from os import environ, path
from dotenv import load_dotenv
load_dotenv(path.join(path.dirname(__file__), ".env"))

from microsoft.agents.hosting.core import AgentApplication
from microsoft.agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app

from .agent import AGENT_APP, CONNECTION_MANAGER

async def entry_point(req: Request) -> Response:
    agent: AgentApplication = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )

APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", entry_point)
APP["agent_configuration"] = CONNECTION_MANAGER
APP["agent_app"] = AGENT_APP
APP["adapter"] = AGENT_APP.adapter

try:
    run_app(APP, host="localhost", port=environ.get("PORT", 3978))
except Exception as error:
    raise error
