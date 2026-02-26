"""
Weather Agent implementation.

Handles incoming messages and uses Azure OpenAI to process
user requests with weather lookup tools.
"""
import json
import traceback
from os import environ
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

from microsoft_agents.hosting.core import TurnContext, TurnState, StoreItem

from tools.weather_tools import get_current_weather_for_location, get_weather_forecast_for_location
from tools.datetime_tools import get_date_time
from telemetry import invoke_observed_agent_operation_with_context

_WELCOME_MESSAGE = "Hello! I'm your Weather Agent. Ask me about the current weather or forecast for any city."
_INSTRUCTIONS = (
    "You are a helpful weather assistant. Use the provided tools to look up "
    "current weather conditions and forecasts for locations requested by the user."
)


_TOOLS = [
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
                        "description": "The city name",
                    },
                    "state": {
                        "type": "string",
                        "description": "The US state name or empty string for international cities",
                    },
                },
                "required": ["location"],
            },
        },
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
                        "description": "The city name",
                    },
                    "state": {
                        "type": "string",
                        "description": "The US state name or empty string for international cities",
                    },
                },
                "required": ["location"],
            },
        },
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
                        "description": "User input (not used)",
                    }
                },
            },
        },
    },
]


class ConversationHistoryStoreItem(StoreItem):
    """Wraps the OpenAI message list so it can be persisted via AgentState."""

    def __init__(self, messages: list = None):
        self.messages = messages or []

    def store_item_to_json(self) -> dict:
        return {"messages": self.messages}

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "ConversationHistoryStoreItem":
        return ConversationHistoryStoreItem(messages=json_data.get("messages", []))


class WeatherAgent:
    """Weather Agent that processes user messages with Azure OpenAI and weather tools."""

    def __init__(self):
        endpoint = environ["AZURE_OPENAI_ENDPOINT"]
        api_version = environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        api_key = environ.get("AZURE_OPENAI_API_KEY")

        if api_key:
            self.openai_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
        else:
            self.openai_client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=DefaultAzureCredential(),
                api_version=api_version,
            )

        self._deployment = environ["AZURE_OPENAI_DEPLOYMENT"]
        self._instructions = environ.get("AGENT_INSTRUCTIONS", _INSTRUCTIONS)
        self._welcome_message = environ.get("AGENT_WELCOME_MESSAGE", _WELCOME_MESSAGE)

        print(f"✅ {environ.get('AGENT_NAME', 'WeatherAgent')} initialized")

    async def send_welcome(self, context: TurnContext, state: TurnState):
        """Send a welcome message to new conversation members."""
        for member in context.activity.members_added or []:
            if member.id != context.activity.recipient.id:
                await context.send_activity(self._welcome_message)

    async def handle_message(self, context: TurnContext, state: TurnState):
        """
        Process an incoming user message.

        Wraps the message logic with A365 observability — equivalent to
        ``A365OtelWrapper.InvokeObservedAgentOperation`` in WeatherAgent.cs.
        """
        user_text = (context.activity.text or "").strip()

        if not user_text:
            return

        print(f"Received: {user_text}")

        async def _process():
            history_item = state.get_value(
                "ConversationState.history",
                lambda: ConversationHistoryStoreItem(),
                target_cls=ConversationHistoryStoreItem,
            )
            conversation_history = history_item.messages
            conversation_history.append({"role": "user", "content": user_text})

            messages = [
                {"role": "system", "content": self._instructions},
                *conversation_history,
            ]

            response = self.openai_client.chat.completions.create(
                model=self._deployment,
                messages=messages,
                tools=_TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                conversation_history.append({
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                })

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"Calling tool: {function_name}({function_args})")

                    if function_name == "get_current_weather_for_location":
                        result = get_current_weather_for_location(
                            location=function_args.get("location", ""),
                            state=function_args.get("state", ""),
                        )
                    elif function_name == "get_weather_forecast_for_location":
                        result = get_weather_forecast_for_location(
                            location=function_args.get("location", ""),
                            state=function_args.get("state", ""),
                        )
                    elif function_name == "get_date_time":
                        result = get_date_time()
                    else:
                        result = f"Unknown function: {function_name}"

                    conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id,
                    })

                second_response = self.openai_client.chat.completions.create(
                    model=self._deployment,
                    messages=[
                        {"role": "system", "content": self._instructions},
                        *conversation_history,
                    ],
                    temperature=0.2,
                )
                final_message = second_response.choices[0].message.content
            else:
                final_message = response_message.content

            conversation_history.append({"role": "assistant", "content": final_message})

            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]

            history_item.messages = conversation_history
            state.set_value("ConversationState.history", history_item)

            await context.send_activity(final_message)
            print("Sent response")

        try:
            await invoke_observed_agent_operation_with_context(
                "OnMessageActivity",
                context,
                state,
                _process,
            )
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            await context.send_activity(f"Sorry, I encountered an error: {str(e)}")
