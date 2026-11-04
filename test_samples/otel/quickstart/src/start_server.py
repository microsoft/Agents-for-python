import logging

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentApplication
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    CloudAdapter,
    jwt_authorization_middleware,
)
from aiohttp.web import Request, Response, Application, run_app

logger = logging.getLogger(__name__)


def start_server(
    agent_application: AgentApplication,
    adapter: CloudAdapter,
    config: Configuration
):
    async def entry_point(req: Request) -> Response:

        logger.info("Request received at /api/messages endpoint.")
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]

        return await start_agent_process(
            req,
            agent,
            adapter,
        )

    APP = Application(middlewares=[jwt_authorization_middleware])
    APP.router.add_post("/api/messages", entry_point)

    APP["agent_configuration"] = config
    APP["agent_app"] = agent_application
    APP["adapter"] = adapter

    run_app(APP, host="localhost", port=config.get_int("PORT", default=3978))
