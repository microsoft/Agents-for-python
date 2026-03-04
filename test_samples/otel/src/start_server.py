from os import environ
import logging

from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app, json_response

from .agent_metrics import agent_metrics

logger = logging.getLogger(__name__)


def start_server(
    agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
    async def entry_point(req: Request) -> Response:

        logger.info("Request received at /api/messages endpoint.")
        text = await req.text()
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]

        with agent_metrics.http_operation("entry_point"):
            return await start_agent_process(
                req,
                agent,
                adapter,
            )

    APP = Application(middlewares=[])
    APP.router.add_post("/api/messages", entry_point)
    # async def health(_req: Request) -> Response:
    #     return json_response(
    #         {
    #             "status": "ok",
    #             "content": "Healthy"
    #         }
    #     )
    # APP.router.add_get("/health", health)

    APP["agent_configuration"] = auth_configuration
    APP["agent_app"] = agent_application
    APP["adapter"] = agent_application.adapter

    try:
        run_app(APP, host="localhost", port=environ.get("PORT", 3978))
    except Exception as error:
        raise error
