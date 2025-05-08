"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from typing import List, Callable, Optional, Dict, Any, Union, Awaitable
import asyncio
from uuid import uuid4

from microsoft.agents.core.models import (
    Activity,
    ConversationReference,
    ResourceResponse,
    ChannelAccount,
    ConversationAccount,
)
from microsoft.agents.builder import Agent, TurnContext, ChannelAdapter


class TestAdapter(ChannelAdapter):
    """
    Test adapter for testing agents.

    This adapter simulates the agent-conversation interaction for testing purposes.
    It can be used to simulate sending and receiving activities to and from an agent.
    """

    def __init__(
        self,
        channel_id: str = "test",
        conversation_id: str = None,
        user_id: str = "user1",
        user_name: str = "Test User",
        bot_id: str = "bot1",
        bot_name: str = "Test Bot",
    ):
        """
        Creates a new TestAdapter instance.

        Args:
            channel_id: The channel ID to use for activities.
            conversation_id: The conversation ID to use for activities. Defaults to a random UUID.
            user_id: The user ID to use for activities sent by the user.
            user_name: The user name to use for activities sent by the user.
            bot_id: The bot ID to use for activities sent by the bot.
            bot_name: The bot name to use for activities sent by the bot.
        """
        self.channel_id = channel_id
        self.conversation_id = conversation_id or str(uuid4())
        self.user_id = user_id
        self.user_name = user_name
        self.bot_id = bot_id
        self.bot_name = bot_name

        # Activities sent back from the bot
        self.sent_activities: List[Activity] = []

        # Create a conversation reference for this adapter
        self.conversation_reference = ConversationReference(
            channel_id=self.channel_id,
            user=ChannelAccount(id=self.user_id, name=self.user_name),
            bot=ChannelAccount(id=self.bot_id, name=self.bot_name),
            conversation=ConversationAccount(id=self.conversation_id),
            service_url="https://test.example.com",
        )

    async def process_activity(
        self, activity: Activity, callback: Callable[[TurnContext], Awaitable]
    ):
        """
        Processes an activity through the agent.

        Args:
            activity: The activity to process.
            callback: The callback to call with the generated TurnContext.

        Returns:
            The result of the callback.
        """
        # Create a TurnContext with the activity
        context = TurnContext(self, activity)

        # Add handler for send activities
        context.on_send_activities(self._record_sent_activities)

        # Call the callback with the TurnContext
        return await callback(context)

    async def _record_sent_activities(self, context, activities, next_handler):
        """
        Records activities sent during testing.

        Args:
            context: The current TurnContext.
            activities: The list of activities being sent.
            next_handler: The next handler to call.

        Returns:
            A list of ResourceResponse objects.
        """
        # Record the activities
        self.sent_activities.extend(activities)

        # Create a ResourceResponse for each activity
        responses = [ResourceResponse(id=str(uuid4())) for _ in activities]

        # Call the next handler
        await next_handler()

        return responses

    async def send_activities(
        self, context: TurnContext, activities: List[Activity]
    ) -> List[ResourceResponse]:
        """
        Sends activities from the bot to the user.

        Args:
            context: The current TurnContext.
            activities: The activities to send.

        Returns:
            A list of ResourceResponse objects.
        """
        # Generate ResourceResponse objects with IDs
        responses = [ResourceResponse(id=str(uuid4())) for _ in activities]

        # Add the activities to the list of sent activities
        self.sent_activities.extend(activities)

        return responses

    async def delete_activity(
        self, context: TurnContext, reference: ConversationReference
    ):
        """
        Deletes an activity.

        Args:
            context: The current TurnContext.
            reference: The ConversationReference for the activity to delete.
        """
        # Find the activity by ID and remove it
        self.sent_activities = [
            a for a in self.sent_activities if a.id != reference.activity_id
        ]

    async def update_activity(self, context: TurnContext, activity: Activity):
        """
        Updates an activity.

        Args:
            context: The current TurnContext.
            activity: The updated activity.

        Returns:
            A ResourceResponse with the ID of the updated activity.
        """
        # Find the activity by ID and update it
        for i, sent in enumerate(self.sent_activities):
            if sent.id == activity.id:
                self.sent_activities[i] = activity
                break

        return ResourceResponse(id=activity.id)

    def create_user_activity(
        self, text: str = None, activity_type: str = "message"
    ) -> Activity:
        """
        Creates a user activity.

        Args:
            text: The text of the activity.
            activity_type: The type of the activity.

        Returns:
            A new Activity configured to be from the user to the bot.
        """
        return Activity(
            id=str(uuid4()),
            type=activity_type,
            text=text,
            from_property=ChannelAccount(id=self.user_id, name=self.user_name),
            recipient=ChannelAccount(id=self.bot_id, name=self.bot_name),
            conversation=ConversationAccount(id=self.conversation_id),
            channel_id=self.channel_id,
        )

    async def test_activity(self, activity: Activity, agent: Agent) -> List[Activity]:
        """
        Processes an activity with the agent and returns the activities sent by the agent.

        Args:
            activity: The activity to process.
            agent: The agent to test.

        Returns:
            The list of activities sent by the agent.
        """
        # Reset sent activities
        self.sent_activities = []

        # Process the activity
        await self.process_activity(activity, agent.on_turn)

        return self.sent_activities

    async def test(self, user_text: str, agent: Agent) -> List[Activity]:
        """
        Tests the agent with a user message and returns the activities sent by the agent.

        Args:
            user_text: The text of the user message.
            agent: The agent to test.

        Returns:
            The list of activities sent by the agent.
        """
        # Create a user activity
        activity = self.create_user_activity(user_text)

        # Test the activity
        return await self.test_activity(activity, agent)

    async def test_conversation(
        self, conversation: List[str], agent: Agent
    ) -> List[List[Activity]]:
        """
        Tests a conversation with the agent.

        Args:
            conversation: The list of user messages to simulate a conversation.
            agent: The agent to test.

        Returns:
            A list of lists of activities sent by the agent in response to each user message.
        """
        responses = []

        # Process each message in the conversation
        for message in conversation:
            # Reset sent activities
            self.sent_activities = []

            # Create a user activity
            activity = self.create_user_activity(message)

            # Process the activity
            await self.process_activity(activity, agent.on_turn)

            # Add the sent activities to the responses
            responses.append(list(self.sent_activities))

        return responses
