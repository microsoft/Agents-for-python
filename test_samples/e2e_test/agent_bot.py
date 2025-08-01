from __future__ import annotations
import re
from typing import Optional, Union
from os import environ

from microsoft.agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory
)
from microsoft.agents.activity import (
    ActivityTypes,
    InvokeResponse,
    Activity,
    ConversationUpdateTypes,
    ChannelAccount, 
    Attachment
)

from agents import (
    Agent as OpenAIAgent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    ModelSettings
)

from pydantic import BaseModel, Field

from tools.get_weather_tool import get_weather
from tools.date_time_tool import get_date

from openai import AsyncAzureOpenAI


class AgentBot:
    def __init__(self, client: AsyncAzureOpenAI):
        self.client = client
        self.multiple_message_pattern = re.compile(r"(\w+)\s+(\d+)")
        self.weather_message_pattern = re.compile(r"^w: .*")
        
    def register_handlers(self, agent_app: AgentApplication[TurnState]):
        """Register all handlers with the agent application"""
        agent_app.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)(self.on_members_added)
        agent_app.message(self.weather_message_pattern)(self.on_weather_message)
        agent_app.message(self.multiple_message_pattern)(self.on_multiple_message)
        agent_app.message(re.compile(r"^poem$"))(self.on_poem_message)
        agent_app.activity(ActivityTypes.message)(self.on_message)
        agent_app.activity(ActivityTypes.invoke)(self.on_invoke)
        
    async def on_members_added(self, context: TurnContext, _state: TurnState):
        await context.send_activity(MessageFactory.text("Hello and Welcome!"))

    async def on_weather_message(self, context: TurnContext, state: TurnState):
            
        class WeatherForecastAgentResponse(BaseModel):
            contentType: str = Field(pattern=r"^(Text|AdaptiveCard)$")
            content: Union[dict, str]
        context.streaming_response.queue_informative_update("Working on a response for you")
                
        agent = OpenAIAgent(
            name="WeatherAgent",
            model_settings=ModelSettings(temperature=0, top_p=1),
            instructions=""""
            You are a friendly assistant that helps people find a weather forecast for a given time and place.
            You may ask follow up questions until you have enough information to answer the customers question,
            but once you have a forecast forecast, make sure to format it nicely using an adaptive card.
            You should use adaptive JSON format to display the information in a visually appealing way
            You should include a button for more details that points at https://www.msn.com/en-us/weather/forecast/in-{location} (replace {location} with the location the user asked about).
            You should use adaptive cards version 1.5 or later.

            Respond in JSON format with the following JSON schema:

            {
                "contentType": "'Text' or 'AdaptiveCard' only",
                "content": "{The content of the response, may be plain text, or JSON based adaptive card}"
            }
            
            Do not include "json" in front of the JSON response.
            """,
            tools=[get_weather, get_date],
        )

        class CustomModelProvider(ModelProvider):
            def get_model(self, model_name: Optional[str]) -> Model:
                return OpenAIChatCompletionsModel(
                    model=model_name or "gpt-4o", 
                    openai_client=self.client,
                    )

        custom_model_provider = CustomModelProvider()

        phrase = context.activity.text.split("w: ", 1)[-1].strip()

        response = await Runner.run(
            agent,
            phrase,
            run_config=RunConfig(
                model_provider=custom_model_provider,
                tracing_disabled=True,
            ),
        )
        
        if "json\n" in response.final_output:
            response.final_output = response.final_output.split("json\n", 1)[-1]

        try:
            llm_response = WeatherForecastAgentResponse.model_validate_json(
                response.final_output
            )
        except:
            llm_response = response.final_output
        
        if type(llm_response) is str:
            activity = MessageFactory.text(llm_response)
            await context.streaming_response.queue_text_chunk(activity)
        else:
            activity = [
                Attachment(
                    content_type="application/vnd.microsoft.card.adaptive",
                    content=llm_response.content,
                )
            ]
            await context.streaming_response.set_attachments(activity)
        
        await context.streaming_response.end_stream()

    async def on_multiple_message(self, context: TurnContext, state: TurnState):
        counter = state.get_value("ConversationState.counter", default_value_factory=(lambda: 0), target_cls=int)

        match = self.multiple_message_pattern.match(context.activity.text)
        if not match:
            return
        word = match.group(1)
        count = int(match.group(2))
        for _ in range(count):
            await context.send_activity(f"[{counter}] You said: {word}")
            counter += 1

        state.set_value("ConversationState.counter", counter)

    async def on_poem_message(self, context: TurnContext, state: TurnState):
        try:
            context.streaming_response.queue_informative_update(
                    "Hold on for an awesome poem about Apollo..."
                )

            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """
                            You are a creative assistant who has deeply studied Greek and Roman Gods, You also know all of the Percy Jackson Series
                            You write poems about the Greek Gods as they are depicted in the Percy Jackson books.
                            You format the poems in a way that is easy to read and understand
                            You break your poems into stanzas 
                            You format your poems in Markdown using double lines to separate stanzas
                        """
                    },
                    {
                        "role": "user",
                        "content": "Write a poem about the Greek God Apollo as depicted in the Percy Jackson books"
                    }
                ],
                stream=True,
                max_tokens=1000
            )
            
            async for update in stream:
                if len(update.choices) > 0:
                    delta = update.choices[0].delta
                    if delta.content:
                        context.streaming_response.queue_text_chunk(delta.content)
        finally:
            await context.streaming_response.end_stream()

    async def on_message(self, context: TurnContext, state: TurnState):
        counter = state.get_value("ConversationState.counter", default_value_factory=(lambda: 0), target_cls=int)
        await context.send_activity(f"[{counter}] You said: {context.activity.text}")
        counter += 1
        state.set_value("ConversationState.counter", counter)

    async def on_invoke(self, context: TurnContext, state: TurnState):
        invoke_response = InvokeResponse(
            status=200, body={"message": "Invoke received.", "data": context.activity.value}
        )
        
        await context.send_activity(
            Activity(type=ActivityTypes.invoke_response, value=invoke_response)
        )
