# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ

from aiohttp.web import Application, Request, Response, middleware, run_app

from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import AgentApplication

from .card_loader import load_resource_text

# The webpage dialog is loaded by Teams in an iframe without a bearer token, so
# it must be reachable without JWT authorization.
_PUBLIC_PATHS = {"/dialog-form"}


@middleware
async def _auth_unless_public(request: Request, handler):
    if request.path in _PUBLIC_PATHS:
        return await handler(request)
    return await jwt_authorization_middleware(request, handler)


def start_server(
    agent_application: AgentApplication,
    auth_configuration,
) -> None:
    async def entry_point(req: Request) -> Response:
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    async def dialog_form(_req: Request) -> Response:
        return Response(
            text=load_resource_text("dialog-form.html"),
            content_type="text/html",
        )

    app = Application(middlewares=[_auth_unless_public])
    app.router.add_post("/api/messages", entry_point)
    app.router.add_get("/api/messages", lambda _: Response(status=200))
    # Served as the URL content for the "Webpage Dialog" task module.
    app.router.add_get("/dialog-form", dialog_form)
    app["agent_configuration"] = auth_configuration
    app["agent_app"] = agent_application
    app["adapter"] = agent_application.adapter

    run_app(app, host="localhost", port=int(environ.get("PORT", 3978)))
