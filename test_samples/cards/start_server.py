# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ

from aiohttp.web import Application, Request, Response, run_app

from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration


def start_server(
    agent_application: AgentApplication,
    auth_configuration: AgentAuthConfiguration,
) -> None:
    async def entry_point(request: Request) -> Response:
        adapter: CloudAdapter = request.app["adapter"]
        agent: AgentApplication = request.app["agent_app"]
        return await start_agent_process(request, agent, adapter)

    web_app = Application(middlewares=[jwt_authorization_middleware])
    web_app.router.add_post("/api/messages", entry_point)
    web_app.router.add_get("/", lambda _: Response(text="Cards sample"))
    web_app["agent_configuration"] = auth_configuration
    web_app["agent_app"] = agent_application
    web_app["adapter"] = agent_application.adapter

    run_app(web_app, host="localhost", port=int(environ.get("PORT", 3978)))
