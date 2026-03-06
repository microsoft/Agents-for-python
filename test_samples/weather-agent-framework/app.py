"""
Weather Agent using Microsoft 365 Agents SDK with aiohttp.
"""
from os import environ, path
from aiohttp import web
from aiohttp.web import Request, Response, Application
from dotenv import load_dotenv

load_dotenv(path.join(path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# OpenTelemetry — configure providers FIRST so that the proxy tracers/meters
# in telemetry/agent_metrics.py resolve to real implementations.
# Equivalent to ConfigureOpenTelemetry() called in Program.cs before building
# the host in the C# sample.
# ---------------------------------------------------------------------------
from telemetry import (
    configure_opentelemetry,
    create_aiohttp_tracing_middleware,
    setup_health_routes,
)

configure_opentelemetry(
    app_name=environ.get("AGENT_NAME", "WeatherAgent"),
    environment=environ.get("ENVIRONMENT", "development"),
    otlp_endpoint=environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
    azure_monitor_connection_string=environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"),
)

# M365 Agents SDK imports
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
    MemoryStorage,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.activity import ActivityTypes, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from agents import WeatherAgent


async def messages_endpoint(request: Request) -> Response:
    """
    Handle POST requests to /api/messages endpoint.

    Args:
        request: The incoming HTTP request.

    Returns:
        HTTP response.
    """
    agent: AgentApplication = request.app["agent_app"]
    adapter: CloudAdapter = request.app["adapter"]

    return await start_agent_process(request, agent, adapter)


def create_app() -> Application:
    """
    Create and configure the aiohttp application.

    Returns:
        Configured aiohttp Application.
    """
    agents_sdk_config = load_configuration_from_env(environ)
    # Create storage
    storage = MemoryStorage()
    
    # Create connection manager for MSAL-based authentication
    connection_manager = MsalConnectionManager(**agents_sdk_config)

    # Create adapter
    adapter = CloudAdapter(connection_manager=connection_manager)
    
    #Create authorization
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)

    # Create agent application
    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config
    )

    # Instantiate our weather agent
    weather_agent = WeatherAgent()

    # Register event handlers
    @agent_app.activity(ActivityTypes.message)
    async def on_message(context: TurnContext, state: TurnState):
        await weather_agent.handle_message(context, state)

    @agent_app.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, state: TurnState):
        await weather_agent.send_welcome(context, state)

    # Create aiohttp app with tracing middleware.
    # Equivalent to AddAspNetCoreInstrumentation() + health-check filter in C#.
    app = Application(middlewares=[create_aiohttp_tracing_middleware(), jwt_authorization_middleware])

    # Add routes
    app.router.add_post("/api/messages", messages_endpoint)
    app.router.add_get("/", lambda _: Response(text="Weather Agent is running", status=200))

    # Register /health and /alive endpoints (development only).
    is_development = environ.get("ENVIRONMENT", "development").lower() == "development"
    setup_health_routes(app, development=is_development)

    # Store agent components
    app["agent_app"] = agent_app
    app["adapter"] = adapter
    app["agent_configuration"] = connection_manager.get_default_connection_configuration()

    return app


def main():
    """Main application entry point."""
    agent_name = environ.get("AGENT_NAME", "WeatherAgent")
    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", 3978))

    print(f"\n{'='*60}")
    print(f"Starting {agent_name} (M365 SDK)")
    print(f"{'='*60}")
    print(f"Endpoint: http://{host}:{port}/api/messages")
    print(f"{'='*60}\n")

    app = create_app()
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
