from os import environ
from microsoft.agents.authorization import AgentAuthConfiguration
from microsoft.agents.builder.app import AgentApplication
from microsoft.agents.hosting.aiohttp import (
    jwt_authorization_middleware,
    start_agent_process,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app
from microsoft.agents.hosting.aiohttp._start_agent_process import start_agent_process


def start_server(
    agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
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
    APP["agent_configuration"] = auth_configuration
    APP["agent_app"] = agent_application
    APP["adapter"] = agent_application.adapter

    try:
        run_app(APP, host="localhost", port=environ.get("PORT", 3978))
    except Exception as error:
        raise error
