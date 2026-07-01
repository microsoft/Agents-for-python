# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ
from pathlib import Path

from aiohttp.web import Application, FileResponse, Request, Response, run_app

from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_decorator,
    start_agent_process,
)
from microsoft_agents.hosting.core import AgentApplication

_STATIC_DIR = Path(__file__).parent.parent / "static"


def start_server(
    agent_application: AgentApplication,
    auth_configuration,
) -> None:
    @jwt_authorization_decorator
    async def entry_point(req: Request):
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    async def serve_settings(_: Request) -> FileResponse:
        return FileResponse(_STATIC_DIR / "settings.html")

    async def health_check(_: Request) -> Response:
        return Response(status=200)

    app = Application()
    app.router.add_post("/api/messages", entry_point)
    app.router.add_get("/api/messages", health_check)
    app.router.add_get("/settings", serve_settings)
    app["agent_configuration"] = auth_configuration
    app["agent_app"] = agent_application
    app["adapter"] = agent_application.adapter

    run_app(app, host="localhost", port=int(environ.get("PORT", 3978)))
