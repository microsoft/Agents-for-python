# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Entra ID Auth Sidecar sample.

Demonstrates wiring the credential-free Entra ID Agent Container (sidecar) auth
provider into an agent using the generic ``ConnectionManager`` with
``provider_factory=SidecarAuth``.
"""

import logging
from os import environ, path

from dotenv import load_dotenv
from aiohttp.web import Request, Response, Application, middleware, run_app

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config._coercion import coerce_bool
from microsoft_agents.authentication.entra_auth_sidecar import SidecarAuth
from microsoft_agents.hosting.core import (
    AgentApplication,
    ConnectionManager,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.authorization import JwtTokenValidator
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)

logging.basicConfig(level=logging.INFO)
load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)


# Mirrors the C# sample's "TokenValidation:Enabled". Inbound channel-token
# validation is DISABLED by default so the sample runs locally against the
# sidecar without a real tenant/app registration. Set TOKENVALIDATION__ENABLED=true
# (and a real CLIENTID/TENANTID) for any non-local deployment.
TOKEN_VALIDATION_ENABLED = coerce_bool(
    environ.get("TOKENVALIDATION__ENABLED", "false"), default=False
)

STORAGE = MemoryStorage()
# No secrets/certificates required: the sidecar owns all credential management.
CONNECTION_MANAGER = ConnectionManager(
    provider_factory=SidecarAuth, **agents_sdk_config
)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


async def _help(context: TurnContext, _state: TurnState):
    await context.send_activity("Welcome!")


AGENT_APP.conversation_update("membersAdded")(_help)
AGENT_APP.message("/help")(_help)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _):
    await context.send_activity(f"**You said:** {context.activity.text}")


async def _health(_req: Request) -> Response:
    # Mirrors the C# sample's "/health" endpoint: reports sidecar reachability.
    provider = CONNECTION_MANAGER.get_default_connection()
    healthy = await provider.is_healthy()
    return Response(status=200 if healthy else 503)


@middleware
async def _anonymous_auth_middleware(request: Request, handler):
    # Development convenience (parity with C# TokenValidation:Enabled=false):
    # skip inbound token validation and inject anonymous claims.
    auth_config = request.app["agent_configuration"]
    request["claims_identity"] = JwtTokenValidator(auth_config).get_anonymous_claims()
    return await handler(request)


def start_server(agent_application: AgentApplication):
    async def entry_point(req: Request) -> Response:
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    auth_middleware = (
        jwt_authorization_middleware
        if TOKEN_VALIDATION_ENABLED
        else _anonymous_auth_middleware
    )
    if not TOKEN_VALIDATION_ENABLED:
        logging.warning(
            "Inbound token validation is DISABLED (TOKENVALIDATION__ENABLED=false). "
            "Enable it for any non-local deployment."
        )

    app = Application(middlewares=[auth_middleware])
    app.router.add_post("/api/messages", entry_point)
    app.router.add_get("/api/messages", lambda _: Response(status=200))
    app.router.add_get("/health", _health)
    app["agent_configuration"] = (
        CONNECTION_MANAGER.get_default_connection_configuration()
    )
    app["agent_app"] = agent_application
    app["adapter"] = agent_application.adapter

    run_app(
        app,
        host=environ.get("HOST", "localhost"),
        port=int(environ.get("PORT", 3978)),
    )


if __name__ == "__main__":
    start_server(AGENT_APP)
