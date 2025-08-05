import json
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
                
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from weather.agents.weather_forecast_agent_response import WeatherForecastAgentResponse
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread

from weather.plugins.date_time_plugin import DateTimePlugin
from weather.plugins.weather_forecast_plugin import WeatherForecastPlugin
from weather.plugins.adaptive_card_plugin import AdaptiveCardPlugin

class WeatherForecastAgent:

    agent_name = "WeatherForecastAgent"
    agent_instructions = """
        You are a friendly assistant that helps people find a weather forecast for a given time and place.
        You may ask follow up questions until you have enough information to answer the customers question,
        but once you have a forecast forecast, make sure to format it nicely using an adaptive card.
        You should use adaptive JSON format to display the information in a visually appealing way
        You should include a button for more details that points at https://www.msn.com/en-us/weather/forecast/in-{location} (replace {location} with the location the user asked about).
        You should use adaptive cards version 1.5 or later.
        
        Respond only in JSON format with the following JSON schema:
        
        {
            "contentType": "'Text' or 'AdaptiveCard' only",
            "content": "{The content of the response, may be plain text, or JSON based adaptive card}"
        }
        """

    def __init__(self):
        self.kernel = Kernel()
        
        execution_settings = OpenAIPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        execution_settings.temperature = 0
        execution_settings.top_p = 1
        
        self.agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name=self.agent_name,
            instructions=self.agent_instructions,
            kernel=self.kernel,
            arguments=KernelArguments(
                chat_history=ChatHistory(),
                settings=execution_settings,
                kernel=self.kernel
            )
        )
        
        self.agent.kernel.add_plugin(
            plugin=DateTimePlugin(),
            plugin_name="datetime"
        )
        self.kernel.add_plugin(
            plugin=AdaptiveCardPlugin(),
            plugin_name="adaptiveCard"
        )
        self.kernel.add_plugin(
            plugin=WeatherForecastPlugin(),
            plugin_name="weatherForecast"
        )
        

    async def invoke_agent_async(self, input: str, chat_history: ChatHistory) -> WeatherForecastAgentResponse:
        
        thread = ChatHistoryAgentThread()
     
        # Add user message to chat history
        chat_history.add_user_message(input)
        
        resp: str = ""

        async for chat in self.agent.invoke(chat_history, thread=thread):
            chat_history.add_message(chat.content)
            resp += chat.content.content

        # if resp has a json\n prefix, remove it
        if "json\n" in resp:
            resp = resp.replace("json\n", "")
            resp = resp.replace("```", "")

        # Format the response
        resp = resp.strip()

        try:
            json_node = json.loads(resp)
            result = WeatherForecastAgentResponse.model_validate(json_node)
            return result
        except Exception as error:
            return await self.invoke_agent_async("That response did not match the expected format. Please try again. Error: " + str(error), chat_history)