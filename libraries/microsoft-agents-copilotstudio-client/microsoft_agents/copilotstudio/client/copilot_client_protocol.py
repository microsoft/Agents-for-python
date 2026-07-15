# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import AsyncIterable, Optional, Protocol
from microsoft_agents.activity import Activity
from .subscribe_event import SubscribeEvent
from .start_request import StartRequest


class CopilotClientProtocol(Protocol):
    """
    Protocol defining the contract for a client that connects to the Direct-to-Engine API endpoint for Copilot Studio.
    """

    async def start_conversation(
        self, emit_start_conversation_event: bool = True
    ) -> AsyncIterable[Activity]:
        """
        Start a new conversation.

        :param emit_start_conversation_event: Whether to emit a start conversation event.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def start_conversation_with_request(
        self, start_request: StartRequest
    ) -> AsyncIterable[Activity]:
        """
        Start a new conversation with a StartRequest.

        :param start_request: The StartRequest containing conversation parameters.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def ask_question(
        self, question: str, conversation_id: Optional[str] = None
    ) -> AsyncIterable[Activity]:
        """
        Ask a question in a conversation.

        :param question: The question text.
        :param conversation_id: Optional conversation ID.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def ask_question_with_activity(
        self, activity: Activity
    ) -> AsyncIterable[Activity]:
        """
        Ask a question using an Activity object.

        :param activity: The activity to send.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def send_activity(self, activity: Activity) -> AsyncIterable[Activity]:
        """
        Send an activity to the bot.

        :param activity: The activity to send.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def execute(
        self, conversation_id: str, activity: Activity
    ) -> AsyncIterable[Activity]:
        """
        Execute an activity with a specified conversation ID.

        :param conversation_id: The conversation ID.
        :param activity: The activity to execute.
        :return: An asynchronous iterable of Activity objects.
        """
        ...

    async def subscribe(
        self, conversation_id: str, last_received_event_id: Optional[str] = None
    ) -> AsyncIterable[SubscribeEvent]:
        """
        Subscribe to conversation events.

        :param conversation_id: The conversation ID to subscribe to.
        :param last_received_event_id: Optional last received event ID for resumption.
        :return: An asynchronous iterable of SubscribeEvent objects.
        """
        ...
