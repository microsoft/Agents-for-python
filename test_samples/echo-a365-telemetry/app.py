# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Echo Agent — Microsoft 365 Agents SDK with full A365 telemetry.

Startup order (mirrors the C# sample):
  1. configure_otel_providers()   — A365 observability framework bootstrap
  2. configure_opentelemetry()    — local TracerProvider / MeterProvider / log bridge
  3. M365 SDK wiring             — storage, adapter, auth, AgentApplication
  4. Route registration           — /api/messages, /health, /alive
"""

import logging
from os import environ, path

from aiohttp import web
from aiohttp.web import Application, Request, Response
from dotenv import load_dotenv

from agent_framework.observability import configure_otel_providers

# Phase 1 — must run before any OTel proxy object is accessed
configure_otel_providers()

logger = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# Phase 2 — set up TracerProvider / MeterProvider / log bridge.
# OTel proxy objects in telemetry/agent_metrics.py resolve to real
# implementations once configure_opentelemetry() has run.
# ---------------------------------------------------------------------------
from telemetry import (
    configure_opentelemetry,
    create_aiohttp_tracing_middleware,
    setup_health_routes,
)

configure_opentelemetry(
    app_name=environ.get("AGENT_NAME", "EchoAgent"),
    environment=environ.get("ENVIRONMENT", "development"),
    otlp_endpoint=environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
    azure_monitor_connection_string=environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"),
)

# ---------------------------------------------------------------------------
# Phase 3 — M365 Agents SDK
# ---------------------------------------------------------------------------
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.activity import ActivityTypes, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager

from echo_agent import EchoAgent


async def messages_endpoint(request: Request) -> Response:
    agent_app: AgentApplication = request.app["agent_app"]
    adapter: CloudAdapter = request.app["adapter"]
    return await start_agent_process(request, agent_app, adapter)


def create_app() -> Application:
    agents_sdk_config = load_configuration_from_env(environ)

    storage = MemoryStorage()
    connection_manager = MsalConnectionManager(**agents_sdk_config)
    adapter = CloudAdapter(connection_manager=connection_manager)
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)

    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config,
    )

    # The echo agent receives user_authorization so the A365 wrapper can cache
    # the observability token — equivalent to injecting IExporterTokenCache in C#.
    echo = EchoAgent(user_authorization=agent_app.auth)

    @agent_app.activity(ActivityTypes.message)
    async def on_message(context: TurnContext, state: TurnState):
        # Pre-fetch the agentic token so it is warm in the cache before the
        # A365 wrapper tries to use it (mirrors the weather agent pattern).
        # await agent_app.auth.get_token(context, "AGENTIC")
        await echo.handle_message(context, state)

    @agent_app.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, state: TurnState):
        await echo.send_welcome(context, state)

    app = Application(
        middlewares=[create_aiohttp_tracing_middleware(), jwt_authorization_middleware]
    )

    app.router.add_post("/api/messages", messages_endpoint)
    app.router.add_get("/", lambda _: Response(text="Echo Agent is running", status=200))

    # Register /health and /alive endpoints (development only).
    is_development = environ.get("ENVIRONMENT", "development").lower() == "development"
    setup_health_routes(app, development=is_development)

    app["agent_app"] = agent_app
    app["adapter"] = adapter
    app["agent_configuration"] = connection_manager.get_default_connection_configuration()

    return app


def main() -> None:
    agent_name = environ.get("AGENT_NAME", "EchoAgent")
    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", 3978))

    print(f"\n{'='*60}")
    print(f"Starting {agent_name} (M365 SDK + A365 Telemetry)")
    print(f"{'='*60}")
    print(f"Endpoint: http://{host}:{port}/api/messages")
    print(f"Health:   http://{host}:{port}/health")
    print(f"Alive:    http://{host}:{port}/alive")
    print(f"{'='*60}\n")

    web.run_app(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
