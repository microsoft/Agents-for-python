import logging

from aiohttp.web import Application, Request, Response, run_app
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentApplication

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

        return await start_agent_process(req, agent, adapter)

    app = Application(middlewares=[jwt_authorization_middleware])
    app.router.add_post("/api/messages", entry_point)

    app["agent_configuration"] = config
    app["agent_app"] = agent_application
    app["adapter"] = adapter

    run_app(app, host="localhost", port=config.get_int("PORT", default=3978))
