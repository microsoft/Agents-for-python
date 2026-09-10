# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""aiohttp hosting for the testing sample."""

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
    adapter: CloudAdapter,
    auth_configuration: AgentAuthConfiguration,
) -> None:
    """Host an AgentApplication at the standard messages endpoint."""

    async def process_messages(request: Request) -> Response:
        application: AgentApplication = request.app["agent_application"]
        request_adapter: CloudAdapter = request.app["adapter"]
        return await start_agent_process(request, application, request_adapter)

    async def health_check(_request: Request) -> Response:
        return Response(status=200, text="OK")

    web_app = Application(middlewares=[jwt_authorization_middleware])
    web_app.router.add_post("/api/messages", process_messages)
    web_app.router.add_get("/api/messages", health_check)
    web_app["agent_configuration"] = auth_configuration
    web_app["agent_application"] = agent_application
    web_app["adapter"] = adapter

    run_app(web_app, host="localhost", port=int(environ.get("PORT", "3978")))
