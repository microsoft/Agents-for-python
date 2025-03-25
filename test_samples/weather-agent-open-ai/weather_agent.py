from microsoft.agents.builder import ActivityHandler, MessageFactory, TurnContext
from microsoft.agents.core.models import ChannelAccount, Attachment

from agents import (
    Agent as OpenAIAgent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    trace,
)
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field

from tools.get_weather_tool import get_weather


class WeatherForecastAgentResponse(BaseModel):
    contentType: str = Field(pattern=r"^(Text|AdaptiveCard)$")
    content: dict


class WeatherAgent(ActivityHandler):
    def __init__(self, client: AsyncAzureOpenAI):
        self.agent = OpenAIAgent(
            name="WeatherAgent",
            instructions=""""
            You are a friendly assistant that helps people find a weather forecast for a given place.
            You may ask follow up questions until you have enough information to answer the customers question,
            but once you have a forecast forecast, make sure to format it nicely using an adaptive card.

            Always respond in JSON format with the following JSON schema, and do not use markdown in the response:

            {
                "contentType": "'Text' if you don't have a forecast or 'AdaptiveCard' if you do",
                "content": "{The content of the response, may be plain text, or JSON based adaptive card}"
            }
            """,
            tools=[get_weather],
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
        with trace("Get Weather", group_id=turn_context.activity.conversation.id):
            response = await Runner.run(
                self.agent,
                turn_context.activity.text,
                run_config=RunConfig(
                    model_provider=self.custom_model_provider,
                    group_id=turn_context.activity.conversation.id,
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
