"""
Weather Agent using Microsoft 365 Agents SDK with aiohttp.
"""
import logging
from os import environ, path
from aiohttp import web
from aiohttp.web import Request, Response, Application
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

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
from telemetry.token_cache import cache_agentic_token


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

    # Register startup handler to prime the observability token cache.
    # Mirrors _setup_observability_token() in host_agent_server.py of the reference sample.
    async def _setup_observability_token(_app: Application) -> None:
        try:
            from microsoft_agents_a365.observability.core.config import get_observability_authentication_scope
        except ImportError:
            logger.debug(
                "A365 observability package not available — skipping observability token setup"
            )
            return

        try:
            config = connection_manager.get_default_connection_configuration()
            tenant_id = config.TENANT_ID
            agent_id = config.CLIENT_ID

            if not tenant_id or not agent_id:
                logger.warning(
                    "Missing TENANT_ID or CLIENT_ID — cannot cache observability token"
                )
                return

            msal_auth = connection_manager.get_default_connection()
            scope = get_observability_authentication_scope()
            scopes = [scope] if isinstance(scope, str) else list(scope)

            token = await msal_auth.get_access_token(
                resource_url=f"https://login.microsoftonline.com/{tenant_id}",
                scopes=scopes,
            )
            cache_agentic_token(tenant_id, agent_id, token)
            logger.info(
                "Observability token cached (tenant=%s, agent=%s)", tenant_id, agent_id
            )
        except Exception as exc:
            logger.warning("Failed to cache observability token: %s", exc)

    app.on_startup.append(_setup_observability_token)

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
