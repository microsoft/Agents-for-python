from __future__ import annotations
import re
from typing import Optional, Union
from os import environ
import json

from microsoft.agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory,
)
from microsoft.agents.activity import (
    ActivityTypes,
    InvokeResponse,
    Activity,
    ConversationUpdateTypes,
    ChannelAccount,
    Attachment,
)

from agents import (
    Agent as OpenAIAgent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    ModelSettings,
)

from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from weather.agents.weather_forecast_agent import WeatherForecastAgent

from openai import AsyncAzureOpenAI


class AgentBot:
    def __init__(self, client: AsyncAzureOpenAI):
        self.client = client
        self.multiple_message_pattern = re.compile(r"(\w+)\s+(\d+)")
        self.weather_message_pattern = re.compile(r"^w: .*")

    def register_handlers(self, agent_app: AgentApplication[TurnState]):
        """Register all handlers with the agent application"""
        agent_app.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)(
            self.on_members_added
        )
        agent_app.message(self.weather_message_pattern)(self.on_weather_message)
        agent_app.message(self.multiple_message_pattern)(self.on_multiple_message)
        agent_app.message(re.compile(r"^poem$"))(self.on_poem_message)
        agent_app.activity(ActivityTypes.message)(self.on_message)
        agent_app.activity(ActivityTypes.invoke)(self.on_invoke)
        agent_app.activity(ActivityTypes.message_update)(self.on_message_edit)
        agent_app.activity(ActivityTypes.event)(self.on_meeting_events)

    async def on_members_added(self, context: TurnContext, _state: TurnState):
        await context.send_activity(MessageFactory.text("Hello and Welcome!"))

    async def on_weather_message(self, context: TurnContext, state: TurnState):

        context.streaming_response.queue_informative_update(
            "Working on a response for you"
        )

        chat_history = state.get_value(
            "ConversationState.chatHistory",
            lambda: ChatHistory(),
            target_cls=ChatHistory,
        )

        weather_agent = WeatherForecastAgent()

        forecast_response = await weather_agent.invoke_agent_async(
            context.activity.text, chat_history
        )
        if forecast_response == None:
            context.streaming_response.queue_text_chunk(
                "Sorry, I couldn't get the weather forecast at the moment."
            )
            await context.streaming_response.end_stream()
            return

        if forecast_response.contentType == "AdaptiveCard":
            context.streaming_response.set_attachments(
                [
                    Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=forecast_response.content,
                    )
                ]
            )
        else:
            context.streaming_response.queue_text_chunk(forecast_response.content)

        await context.streaming_response.end_stream()

    async def on_multiple_message(self, context: TurnContext, state: TurnState):
        counter = state.get_value(
            "ConversationState.counter",
            default_value_factory=(lambda: 0),
            target_cls=int,
        )

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
                        """,
                    },
                    {
                        "role": "user",
                        "content": "Write a poem about the Greek God Apollo as depicted in the Percy Jackson books",
                    },
                ],
                stream=True,
                max_tokens=1000,
            )

            async for update in stream:
                if len(update.choices) > 0:
                    delta = update.choices[0].delta
                    if delta.content:
                        context.streaming_response.queue_text_chunk(delta.content)
        finally:
            await context.streaming_response.end_stream()

    async def on_message(self, context: TurnContext, state: TurnState):
        counter = state.get_value(
            "ConversationState.counter",
            default_value_factory=(lambda: 0),
            target_cls=int,
        )
        await context.send_activity(f"[{counter}] You said: {context.activity.text}")
        counter += 1
        state.set_value("ConversationState.counter", counter)

    async def on_invoke(self, context: TurnContext, state: TurnState):

        # Simulate Teams extensions until implemented
        if context.activity.name == "composeExtension/query":
            invoke_response = InvokeResponse(
                status=200,
                body={
                    "ComposeExtension": {
                        "type": "result",
                        "AttachmentLayout": "list",
                        "Attachments": [
                            {"content_type": "test", "content_url": "example.com"}
                        ],
                    }
                },
            )

            await context.send_activity(
                Activity(type=ActivityTypes.invoke_response, value=invoke_response)
            )
        elif context.activity.name == "composeExtension/queryLink":
            invoke_response = InvokeResponse(
                status=200,
                body={
                    "ChannelId": "msteams",
                    "ComposeExtension": {
                        "type": "result",
                        "text": "On Query Link",
                    },
                },
            )
            await context.send_activity(
                Activity(type=ActivityTypes.invoke_response, value=invoke_response)
            )
        elif context.activity.name == "composeExtension/selectItem":
            value = context.activity.value
            invoke_response = InvokeResponse(
                status=200,
                body={
                    "ChannelId": "msteams",
                    "ComposeExtension": {
                        "type": "result",
                        "AttachmentLayout": "list",
                        "Attachments": [
                            {
                                "contenttype": "application/vnd.microsoft.card.thumbnail",
                                "content": {
                                    "title": f"{value["id"]}, {value["version"]}"
                                },
                            }
                        ],
                    },
                },
            )
            await context.send_activity(
                Activity(type=ActivityTypes.invoke_response, value=invoke_response)
            )
        else:
            invoke_response = InvokeResponse(
                status=200,
                body={"message": "Invoke received.", "data": context.activity.value},
            )

            await context.send_activity(
                Activity(type=ActivityTypes.invoke_response, value=invoke_response)
            )

    async def on_message_edit(self, context: TurnContext, state: TurnState):
        await context.send_activity(f"Message Edited: {context.activity.id}")

    async def on_meeting_events(self, context: TurnContext, state: TurnState):
        if context.activity.name == "application/vnd.microsoft.meetingStart":
            await context.send_activity(
                f"Meeting started with ID: {context.activity.value["id"]}"
            )
        elif context.activity.name == "application/vnd.microsoft.meetingEnd":
            await context.send_activity(
                f"Meeting ended with ID: {context.activity.value["id"]}"
            )
        elif (
            context.activity.name == "application/vnd.microsoft.meetingParticipantJoin"
        ):
            await context.send_activity("Welcome to the meeting!")
