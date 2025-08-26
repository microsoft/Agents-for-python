from __future__ import annotations

from typing import Union
from microsoft.agents.hosting.core import ActivityHandler, MessageFactory, TurnContext
from microsoft.agents.activity import ChannelAccount, Attachment

from agents import (
    Agent as OpenAIAgent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
)
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field

from tools.get_weather_tool import get_weather
from tools.date_time_tool import get_date


class WeatherForecastAgentResponse(BaseModel):
    contentType: str = Field(pattern=r"^(Text|AdaptiveCard)$")
    content: Union[dict, str]


class WeatherAgent(ActivityHandler):
    def __init__(self, client: AsyncAzureOpenAI):
        self.agent = OpenAIAgent(
            name="WeatherAgent",
            instructions=""""
            You are a friendly assistant that helps people find a weather forecast for a given time and place.
            Do not reply with MD format nor plain text. You can ONLY respond in JSON format with the following JSON schema
            {
                "contentType": "'Text' if you don't have a forecast or 'AdaptiveCard' if you do",
                "content": "{The content of the response, may be plain text, or JSON based adaptive card}"
            }
            You may ask follow up questions until you have enough information to answer the customers question,
            but once you have a forecast forecast, make sure to format it nicely using an adaptive card.
            """,
            tools=[get_weather, get_date],
        )

        class CustomModelProvider(ModelProvider):
            def get_model(self, model_name: str | None) -> Model:
                return OpenAIChatCompletionsModel(
                    model=model_name or "gpt-4o", openai_client=client
                )

        self.custom_model_provider = CustomModelProvider()

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        response = await Runner.run(
            self.agent,
            turn_context.activity.text,
            run_config=RunConfig(
                model_provider=self.custom_model_provider,
                tracing_disabled=True,
            ),
        )

        llm_response = WeatherForecastAgentResponse.model_validate_json(
            response.final_output
        )
        if llm_response.contentType == "AdaptiveCard":
            activity = MessageFactory.attachment(
                Attachment(
                    content_type="application/vnd.microsoft.card.adaptive",
                    content=llm_response.content,
                )
            )
        elif llm_response.contentType == "Text":
            activity = MessageFactory.text(llm_response.content)

        return await turn_context.send_activity(activity)
