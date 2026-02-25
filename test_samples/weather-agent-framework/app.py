"""
Weather Agent using Microsoft 365 Agents SDK with aiohttp.

This approach is closer to the C# implementation and supports Teams/M365 integration.
Uses the microsoft-agents-hosting-aiohttp package for web endpoint hosting.
"""
import sys
import os
from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response, Application
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

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
    invoke_observed_agent_operation_with_context,
)

# config is imported here so the settings are available for configure_opentelemetry
# (the full 'from config import settings' import happens below after the SDK block)
from config import settings as _early_settings

configure_opentelemetry(
    app_name=_early_settings.agent_name,
    environment=os.environ.get("ENVIRONMENT", "development"),
    otlp_endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
    azure_monitor_connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"),
)

# M365 Agents SDK imports
# Note: Import structure may vary based on actual package implementation
# This is a conceptual implementation based on the C# patterns
try:
    from microsoft_agents.hosting.core import (
        AgentApplication,
        TurnContext,
        TurnState,
        MemoryStorage,
        ActivityHandler,
    )
    from microsoft_agents.hosting.aiohttp import (
        CloudAdapter,
        start_agent_process,
    )
    from microsoft_agents.activity import Activity, ActivityTypes
except ImportError:
    print("⚠️ Microsoft Agents SDK packages not found.")
    print("This implementation requires:")
    print("  - microsoft-agents-hosting-aiohttp")
    print("  - microsoft-agents-hosting-core")
    print("\nInstall with: pip install microsoft-agents-hosting-aiohttp")
    print("\nNote: Using conceptual implementation based on C# patterns.")
    print("The actual API may differ. Refer to official documentation.\n")
    sys.exit(1)

from config import settings
from tools.weather_tools import get_current_weather_for_location, get_weather_forecast_for_location
from tools.datetime_tools import get_date_time

# Suppress the early-import alias now that the real settings object is imported
del _early_settings


class WeatherAgent(ActivityHandler):
    """
    Weather Agent implementation similar to the C# WeatherAgent class.

    This agent handles incoming messages and uses Azure OpenAI to process
    user requests with weather lookup tools.
    """

    def __init__(self):
        """Initialize the Weather Agent."""
        super().__init__()

        # Validate configuration
        settings.validate_required_settings()

        # Initialize Azure OpenAI client
        if settings.azure_openai_api_key:
            self.openai_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
        else:
            self.openai_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_ad_token_provider=DefaultAzureCredential(),
                api_version=settings.azure_openai_api_version,
            )

        print(f"✅ {settings.agent_name} initialized")

    async def on_members_added_activity(self, context: TurnContext, state: TurnState):
        """
        Handle members added to conversation (similar to C# WelcomeMessageAsync).

        Args:
            context: The turn context for this activity.
            state: The turn state.
        """
        for member in context.activity.members_added or []:
            if member.id != context.activity.recipient.id:
                await context.send_activity(settings.agent_welcome_message)

    async def on_message_activity(self, context: TurnContext, state: TurnState):
        """
        Handle incoming message activities (similar to C# OnMessageAsync).

        Wraps the message logic with A365 observability — equivalent to the
        ``A365OtelWrapper.InvokeObservedAgentOperation`` call in WeatherAgent.cs.

        Args:
            context: The turn context for this message.
            state: The turn state.
        """
        user_text = (context.activity.text or "").strip()

        if not user_text:
            return

        print(f"Received: {user_text}")

        async def _handle_message():
            # Build conversation history from state
            conversation_history = state.conversation.get("history", [])

            # Add user message
            conversation_history.append({
                "role": "user",
                "content": user_text
            })

            # Prepare tools for Azure OpenAI
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_weather_for_location",
                        "description": "Retrieves the current weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city name"
                                },
                                "state": {
                                    "type": "string",
                                    "description": "The US state name or empty string for international cities"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather_forecast_for_location",
                        "description": "Retrieves the 5-day weather forecast for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city name"
                                },
                                "state": {
                                    "type": "string",
                                    "description": "The US state name or empty string for international cities"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_date_time",
                        "description": "Get the current date and time",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input_text": {
                                    "type": "string",
                                    "description": "User input (not used)"
                                }
                            }
                        }
                    }
                }
            ]

            # Call Azure OpenAI with function calling
            messages = [
                {"role": "system", "content": settings.agent_instructions},
                *conversation_history
            ]

            response = self.openai_client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Handle tool calls
            if tool_calls:
                # Add assistant message with tool calls
                conversation_history.append({
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                })

                # Execute tool calls
                import json
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"Calling tool: {function_name}({function_args})")

                    if function_name == "get_current_weather_for_location":
                        function_response = get_current_weather_for_location(
                            location=function_args.get("location", ""),
                            state=function_args.get("state", "")
                        )
                    elif function_name == "get_weather_forecast_for_location":
                        function_response = get_weather_forecast_for_location(
                            location=function_args.get("location", ""),
                            state=function_args.get("state", "")
                        )
                    elif function_name == "get_date_time":
                        function_response = get_date_time()
                    else:
                        function_response = f"Unknown function: {function_name}"

                    # Add function response to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": function_response,
                        "tool_call_id": tool_call.id
                    })

                # Get final response from model
                second_response = self.openai_client.chat.completions.create(
                    model=settings.azure_openai_deployment,
                    messages=[
                        {"role": "system", "content": settings.agent_instructions},
                        *conversation_history
                    ],
                    temperature=0.2,
                )

                final_message = second_response.choices[0].message.content
            else:
                final_message = response_message.content

            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

            # Keep last 10 messages in history
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]

            # Save conversation history to state
            state.conversation["history"] = conversation_history

            # Send response
            await context.send_activity(final_message)
            print("Sent response")

        # Wrap the message handler with A365 observability — equivalent to
        # A365OtelWrapper.InvokeObservedAgentOperation() in WeatherAgent.cs.
        # Any exception propagates after being recorded on the span.
        try:
            await invoke_observed_agent_operation_with_context(
                "OnMessageActivity",
                context,
                state,
                _handle_message,
            )
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await context.send_activity(error_msg)


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
    # Create storage
    storage = MemoryStorage()

    # Create adapter
    adapter = CloudAdapter()

    # Create agent application
    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
    )

    # Instantiate our weather agent
    weather_agent = WeatherAgent()

    # Register event handlers
    @agent_app.activity(ActivityTypes.MESSAGE)
    async def on_message(context: TurnContext, state: TurnState):
        await weather_agent.on_message_activity(context, state)

    @agent_app.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, state: TurnState):
        await weather_agent.on_members_added_activity(context, state)

    # Create aiohttp app with tracing middleware.
    # Equivalent to AddAspNetCoreInstrumentation() + health-check filter in C#.
    app = Application(middlewares=[create_aiohttp_tracing_middleware()])

    # Add routes
    app.router.add_post("/api/messages", messages_endpoint)
    app.router.add_get("/", lambda _: Response(text="Weather Agent is running", status=200))

    # Register /health and /alive endpoints (development only).
    # Equivalent to app.MapDefaultEndpoints() in C#.
    is_development = os.environ.get("ENVIRONMENT", "development").lower() == "development"
    setup_health_routes(app, development=is_development)

    # Store agent components
    app["agent_app"] = agent_app
    app["adapter"] = adapter

    return app


def main():
    """Main application entry point."""
    try:
        settings.validate_required_settings()
    except ValueError as e:
        print(f"\n❌ Configuration Error:\n{e}\n")
        print("Please create a .env file based on .env.example and configure required settings.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"🤖 Starting {settings.agent_name} (M365 SDK)")
    print(f"{'='*60}")
    print(f"Endpoint: http://{settings.host}:{settings.port}/api/messages")
    print(f"{'='*60}\n")

    app = create_app()
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
