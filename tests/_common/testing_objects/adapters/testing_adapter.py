# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional, Awaitable
from collections import deque

from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    Channels,
    ResourceResponse,
    RoleTypes,
    InvokeResponse,
)
from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter
from microsoft_agents.hosting.core.turn_context import TurnContext

from ..testing_user_token_client import TestingUserTokenClient

AgentCallbackHandler = Callable[[TurnContext], Awaitable]


class TestingAdapter(ChannelAdapter):
    """
    A mock adapter that can be used for unit testing of agent logic.
    """

    def __init__(
        self,
        channel_id: str = None,
        conversation: ConversationReference = None,
        send_trace_activity: bool = False,
        logger=None,
    ):
        """
        Initializes a new instance of the TestingAdapter class.

        Args:
            channel_id: The target channel for the test that will be passed to the agent.
            conversation: A reference to the conversation to begin the adapter state with.
            send_trace_activity: Indicates whether the adapter should add trace activities.
            logger: Logger for this class.
        """
        super().__init__()
        self._send_trace_activity = send_trace_activity
        self._conversation_lock = asyncio.Lock()
        self._active_queue_lock = asyncio.Lock()
        self._user_token_client = TestingUserTokenClient()

        self._next_id = 0
        self._queued_requests = deque()

        if conversation is not None:
            self.conversation = conversation
        else:
            self.conversation = ConversationReference(
                channel_id=channel_id or Channels.test,
                service_url="https://test.com",
                user=ChannelAccount(id="user1", name="User1"),
                agent=ChannelAccount(id="agent", name="Agent"),
                conversation=ConversationAccount(
                    is_group=False, id="convo1", name="Conversation1"
                ),
                locale=self.locale,
            )

        # Active queue to store agent responses
        self.active_queue = deque()

        # Identity for the adapter
        self.claims_identity = ClaimsIdentity({}, True)

    @property
    def enable_trace(self) -> bool:
        """
        Gets or sets a value indicating whether to send trace activities.
        """
        return self._send_trace_activity

    @enable_trace.setter
    def enable_trace(self, value: bool):
        self._send_trace_activity = value

    @property
    def locale(self) -> str:
        """
        Gets or sets the locale for the conversation.
        """
        return getattr(self, "_locale", "en-us")

    @locale.setter
    def locale(self, value: str):
        self._locale = value

    @staticmethod
    def create_conversation(
        name: str, user: str = "User1", agent: str = "Agent"
    ) -> ConversationReference:
        """
        Create a ConversationReference.

        Args:
            name: Name of the conversation (also ID).
            user: Name of the user (also ID) default: User1.
            agent: Name of the agent (also ID) default: Agent.

        Returns:
            A ConversationReference object.
        """
        return ConversationReference(
            channel_id="test",
            service_url="https://test.com",
            conversation=ConversationAccount(is_group=False, id=name, name=name),
            user=ChannelAccount(id=user.lower(), name=user),
            bot=ChannelAccount(id=agent.lower(), name=agent),
            locale="en-us",
        )

    def use(self, middleware):
        """
        Adds middleware to the adapter's pipeline.

        Args:
            middleware: The middleware to add.

        Returns:
            The updated adapter object.
        """
        super().use(middleware)
        return self

    async def process_activity_async(
        self,
        activity: Activity,
        callback: AgentCallbackHandler,
        claims_identity: ClaimsIdentity = None,
    ):
        """
        Process an activity through the adapter.

        Args:
            activity: Activity to process.
            callback: Agent logic to invoke.
            claims_identity: Claims identity for the activity.

        Returns:
            Invoke response.
        """
        identity = claims_identity or self.claims_identity
        return await self.process_activity(identity, activity, callback)

    async def process_activity(
        self,
        claims_identity: ClaimsIdentity,
        activity: Activity,
        callback: AgentCallbackHandler,
    ) -> InvokeResponse:
        """
        Receives an activity and runs it through the middleware pipeline.

        Args:
            claims_identity: Claims identity for the activity.
            activity: The activity to process.
            callback: The agent logic to invoke.

        Returns:
            Invoke response.
        """
        async with self._conversation_lock:
            # Ready for next reply
            if activity.type is None:
                activity.type = ActivityTypes.message

            if activity.channel_id is None:
                activity.channel_id = self.conversation.channel_id

            if (
                activity.from_property is None
                or activity.from_property.id == "unknown"
                or activity.from_property.role == RoleTypes.agent
            ):
                activity.from_property = self.conversation.user

            activity.recipient = self.conversation.agent
            activity.conversation = self.conversation.conversation
            activity.service_url = self.conversation.service_url

            id_str = str(self._next_id)
            activity.id = id_str
            self._next_id += 1

        # Set timestamps if not provided
        if activity.timestamp is None:
            activity.timestamp = datetime.now(timezone.utc)

        if activity.local_timestamp is None:
            activity.local_timestamp = datetime.now()

        # Create context and run pipeline
        context = self.create_turn_context(activity)
        await self.run_pipeline(context, callback)

        return None

    async def process_proactive(
        self,
        claims_identity: ClaimsIdentity,
        continuation_activity: Activity,
        audience: str,
        callback: AgentCallbackHandler,
    ):
        """
        Process a proactive message.

        Args:
            claims_identity: A ClaimsIdentity for the conversation.
            continuation_activity: The continuation Activity used to create the TurnContext.
            audience: The audience for the call.
            callback: The method to call for the resulting agent turn.

        Returns:
            A task representing the work queued to execute.
        """
        context = self.create_turn_context(continuation_activity)
        await self.run_pipeline(context, callback)

    async def send_activities(
        self, turn_context: TurnContext, activities: List[Activity]
    ) -> List[ResourceResponse]:
        """
        Sends activities to the conversation.

        Args:
            turn_context: Context for the current turn of conversation.
            activities: The activities to send.

        Returns:
            An array of ResourceResponse objects containing the IDs assigned to the activities.
        """
        if turn_context is None:
            raise TypeError("turn_context cannot be None")

        if activities is None:
            raise TypeError("activities cannot be None")

        if len(activities) == 0:
            raise ValueError(
                "Expecting one or more activities, but the array was empty."
            )

        responses = []

        for activity in activities:
            if not activity.id:
                activity.id = str(uuid.uuid4())

            if activity.timestamp is None:
                activity.timestamp = datetime.now(timezone.utc)

            if activity.type == ActivityTypes.trace:
                if self._send_trace_activity:
                    await self._enqueue(activity)
            else:
                await self._enqueue(activity)

            responses.append(ResourceResponse(id=activity.id))

        return responses

    async def update_activity(
        self, turn_context: TurnContext, activity: Activity
    ) -> ResourceResponse:
        """
        Replaces an existing activity in the active queue.

        Args:
            turn_context: Context for the current turn of conversation.
            activity: New replacement activity.

        Returns:
            A ResourceResponse object containing the ID assigned to the activity.
        """
        async with self._active_queue_lock:
            replies = list(self.active_queue)
            for i in range(len(self.active_queue)):
                if replies[i].id == activity.id:
                    replies[i] = activity
                    self.active_queue.clear()
                    for item in replies:
                        self.active_queue.append(item)

                    return ResourceResponse(id=activity.id)

        return ResourceResponse()

    async def delete_activity(
        self, turn_context: TurnContext, reference: ConversationReference
    ):
        """
        Deletes an existing activity in the active queue.

        Args:
            turn_context: Context for the current turn of conversation.
            reference: Conversation reference for the activity to delete.

        Returns:
            A task representing the work queued to execute.
        """
        async with self._active_queue_lock:
            replies = list(self.active_queue)
            for i in range(len(self.active_queue)):
                if replies[i].id == reference.activity_id:
                    replies.pop(i)
                    self.active_queue.clear()
                    for item in replies:
                        self.active_queue.append(item)
                    break

    async def create_conversation_async(
        self, channel_id: str, callback: AgentCallbackHandler
    ):
        """
        Creates a new conversation on the specified channel.

        Args:
            channel_id: The ID of the channel.
            callback: The agent logic to call when the conversation is created.

        Returns:
            A task representing the work queued to execute.
        """
        self.active_queue.clear()
        update = Activity.create_conversation_update_activity()
        update.channel_id = channel_id
        update.conversation = ConversationAccount(id=str(uuid.uuid4()))

        context = self.create_turn_context(update)
        await callback(context)

    def get_next_reply(self) -> Optional[Activity]:
        """
        Dequeues and returns the next agent response from the active queue.

        Returns:
            The next activity in the queue; or None, if the queue is empty.
        """
        if len(self.active_queue) > 0:
            return self.active_queue.popleft()

        return None

    async def get_next_reply_async(self) -> Activity:
        """
        Get the next reply asynchronously.

        Returns:
            Activity when it's available or None if canceled.
        """
        async with self._active_queue_lock:
            if not self._queued_requests:
                result = self.get_next_reply()
                if result is not None:
                    return result

            # Create a future for the next reply
            future = asyncio.Future()
            self._queued_requests.append(future)

        # Wait for the future to be completed outside the lock
        return await future

    def make_activity(self, text: str = None) -> Activity:
        """
        Creates a message activity from text and the current conversational context.

        Args:
            text: The message text.

        Returns:
            An appropriate message activity.
        """
        activity = Activity(
            type=ActivityTypes.message,
            locale=self.locale,
            from_property=self.conversation.user,
            recipient=self.conversation.agent,
            conversation=self.conversation.conversation,
            service_url=self.conversation.service_url,
            id=str(self._next_id),
            text=text,
        )

        self._next_id += 1
        return activity

    async def send_text_to_agent_async(
        self, user_says: str, callback: AgentCallbackHandler
    ):
        """
        Processes a message activity from a user.

        Args:
            user_says: The text of the user's message.
            callback: The turn processing logic to use.

        Returns:
            A task representing the work queued to execute.
        """
        return await self.process_activity_async(
            self.make_activity(user_says), callback
        )

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str = None,
    ):
        """
        Adds a fake user token so it can later be retrieved.

        Args:
            connection_name: The connection name.
            channel_id: The channel ID.
            user_id: The user ID.
            token: The token to store.
            magic_code: The optional magic code to associate with this token.
        """
        self._user_token_client.add_user_token(
            connection_name, channel_id, user_id, token, magic_code
        )

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ):
        """
        Adds a fake exchangeable token so it can be exchanged later.

        Args:
            connection_name: The connection name.
            channel_id: The channel ID.
            user_id: The user ID.
            exchangeable_item: The exchangeable token or resource URI.
            token: The token to store.
        """
        self._user_token_client.add_exchangeable_token(
            connection_name, channel_id, user_id, exchangeable_item, token
        )

    def throw_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ):
        """
        Adds an instruction to throw an exception during exchange requests.

        Args:
            connection_name: The connection name.
            channel_id: The channel ID.
            user_id: The user ID.
            exchangeable_item: The exchangeable token or resource URI.
        """
        self._user_token_client.throw_on_exchange_request(
            connection_name, channel_id, user_id, exchangeable_item
        )

    def create_turn_context(
        self, activity: Activity, identity: ClaimsIdentity = None
    ) -> TurnContext:
        """
        Creates the turn context for the adapter.

        Args:
            activity: An Activity instance for the turn.
            identity: The claims identity.

        Returns:
            A TurnContext instance to be used by the adapter.
        """
        turn_context = TurnContext(self, activity)

        turn_context.services["UserTokenClient"] = self._user_token_client
        turn_context._identity = identity or self.claims_identity

        return turn_context

    async def test(self, msg: str, callback: AgentCallbackHandler) -> List[Activity]:
        """
        Run a test, sending a message to a agent and returning the responses received.

        Args:
            msg: The message to send.
            callback: The agent turn logic.

        Returns:
            A list of activities returned from the agent in response to the message.
        """
        # Clear the active queue
        self.active_queue.clear()

        # Send the message
        await self.send_text_to_agent_async(msg, callback)

        # Collect all the responses
        responses = []
        response = self.get_next_reply()
        while response is not None:
            responses.append(response)
            response = self.get_next_reply()

        return responses

    async def _enqueue(self, activity: Activity):
        """
        Adds an activity to the end of the queue or fulfills a pending request.

        Args:
            activity: The activity to add to the queue.
        """
        async with self._active_queue_lock:
            # If there are pending requests, fulfill them with the activity
            if self._queued_requests:
                future = self._queued_requests.popleft()
                if not future.done():
                    future.set_result(activity)
                    return

            # Otherwise enqueue for the next requester
            self.active_queue.append(activity)
