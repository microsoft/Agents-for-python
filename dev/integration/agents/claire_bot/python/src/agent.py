from __future__ import annotations
import json
import re

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory
)
from microsoft_agents.activity import (
    ActivityTypes,
    InvokeResponse,
    Activity,
    ConversationUpdateTypes,
    Attachment,
    EndOfConversationCodes,
    DeliveryModes
)

from microsoft_agents.hosting.teams import TeamsActivityHandler


from semantic_kernel.contents import ChatHistory
from .weather.agents.weather_forecast_agent import WeatherForecastAgent

from openai import AsyncAzureOpenAI
import asyncio

class Agent():
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
        agent_app.message(re.compile(r"^end$"))(self.on_end_message)
        agent_app.message(re.compile(r"^stream$"))(self.on_stream_message)
        agent_app.activity(ActivityTypes.message)(self.on_message)
        agent_app.activity(ActivityTypes.invoke)(self.on_invoke)
        agent_app.message_reaction("reactionsAdded")(self.on_reaction_added)
        agent_app.message_reaction("reactionsRemoved")(self.on_reaction_removed)
        agent_app.activity(ActivityTypes.message_update)(self.on_message_edit)
        agent_app.activity(ActivityTypes.event)(self.on_event)
        
    async def on_members_added(self, context: TurnContext, _state: TurnState):
        await context.send_activity(MessageFactory.text("Hello and Welcome!"))

    async def on_stream_message(self, context: TurnContext, state: TurnState):
        if context.activity.delivery_mode == DeliveryModes.stream:
            for x in range(1, 5):
                await asyncio.sleep(1)
                await context.send_activity("Stream response " + str(x))
        else:
            await context.send_activity("Activity is not set to stream for delivery mode")

    async def on_weather_message(self, context: TurnContext, state: TurnState):
        
        context.streaming_response.queue_informative_update("Working on a response for you")

        chat_history = state.get_value(
            "ConversationState.chatHistory", 
            lambda: ChatHistory(), 
            target_cls=ChatHistory
            )
                
        weather_agent = WeatherForecastAgent()

        forecast_response = await weather_agent.invoke_agent(context.activity.text, chat_history)
        if forecast_response == None:
            context.streaming_response.queue_text_chunk("Sorry, I couldn't get the weather forecast at the moment.")
            await context.streaming_response.end_stream()
            return
        
        if forecast_response.contentType == "AdaptiveCard":
            context.streaming_response.set_attachments(
                [
                    Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=forecast_response.content
                    )
                ]
            )
        else:
            context.streaming_response.queue_text_chunk(forecast_response.content)

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
        await state.save(context)

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
            
    async def on_end_message(self, context: TurnContext, state: TurnState):
        await context.send_activity("Ending conversation...")
        
        endOfConversation = Activity.create_end_of_conversation_activity()
        endOfConversation.code = EndOfConversationCodes.completed_successfully
        await context.send_activity(endOfConversation)
        
    # Simulate a message handler for Action.Submit
    # Waiting for Teams Extension to support Action.Submit
    async def on_action_submit(self, context: TurnContext, state: TurnState):
        user_text = context.activity.value.get("usertext", "")
        if not user_text:
            await context.send_activity("No user text provided in the action submit.")
            return
        await context.send_activity("doStuff action submitted " + json.dumps(context.activity.value))

    async def on_action_execute(self, context: TurnContext, state: TurnState):
        action = context.activity.value.get("action", {})
        data = action.get("data", {})
        user_text = data.get("usertext", "")
        
        if not user_text:
            await context.send_activity("No user text provided in the action execute.")
            return
 
        invoke_response = InvokeResponse(
            status=200,
            body={
                "statusCode": 200,
                "type": "application/vnd.microsoft.card.adaptive",
                "value": {
                    "usertext": user_text
                }
            }
        )

        await context.send_activity(
            Activity(type=ActivityTypes.invoke_response, value=invoke_response)
        )
        
    async def on_reaction_added(self, context: TurnContext, state: TurnState):
        await context.send_activity("Message Reaction Added: " + context.activity.reactions_added[0].type)
    
    async def on_reaction_removed(self, context: TurnContext, state: TurnState):
        await context.send_activity("Message Reaction Removed: " + context.activity.reactions_removed[0].type)

    async def on_message(self, context: TurnContext, state: TurnState):
        
        if context.activity.value and context.activity.value.get("verb") == "doStuff":
            await self.on_action_submit(context, state)
            return
        
        counter = state.get_value("ConversationState.counter", default_value_factory=(lambda: 0), target_cls=int)
        await context.send_activity(f"[{counter}] You said: {context.activity.text}")
        counter += 1
        state.set_value("ConversationState.counter", counter)
        
        await state.save(context)

    async def on_invoke(self, context: TurnContext, state: TurnState):

        # Simulate Teams extensions until implemented
        if context.activity.name == "adaptiveCard/action":
            await self.on_action_execute(context, state)
        elif context.activity.name == "composeExtension/query":
            invoke_response = InvokeResponse(
                status=200,
                body={
                    "composeExtension": {
                        "type": "result",
                        "attachmentLayout": "list",
                        "attachments": [
                            {"contentType": "test", "contentUrl": "example.com"}
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
                    "channelId": "msteams",
                    "composeExtension": {
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
                    "channelId": "msteams",
                    "composeExtension": {
                        "type": "result",
                        "attachmentLayout": "list",
                        "attachments": [
                            {
                                "contentType": "application/vnd.microsoft.card.thumbnail",
                                "content": {
                                    "title": f"{value['id']}, {value['version']}"
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

    async def on_event(self, context: TurnContext, state: TurnState):
        if context.activity.name == "application/vnd.microsoft.meetingStart":
            await context.send_activity(
                f"Meeting started with ID: {context.activity.value['id']}"
            )
        elif context.activity.name == "application/vnd.microsoft.meetingEnd":
            await context.send_activity(
                f"Meeting ended with ID: {context.activity.value['id']}"
            )
        elif context.activity.name == "application/vnd.microsoft.meetingParticipantJoin":
            await context.send_activity("Welcome to the meeting!")
        else:
            await context.send_activity("Received an event: " + context.activity.name)

