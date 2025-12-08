# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import aiohttp
from typing import AsyncIterable, Callable, Optional

from microsoft_agents.activity import Activity, ActivityTypes, ConversationAccount

from .connection_settings import ConnectionSettings
from .execute_turn_request import ExecuteTurnRequest
from .power_platform_environment import PowerPlatformEnvironment


class CopilotClient:
    """A client for interacting with the Copilot service."""

    EVENT_STREAM_TYPE = "text/event-stream"
    APPLICATION_JSON_TYPE = "application/json"

    _current_conversation_id = ""

    def __init__(
        self,
        settings: ConnectionSettings,
        token: str,
    ):
        self.settings = settings
        self._token = token
        # TODO: Add logger
        # self.logger = logger
        self.conversation_id = ""

    async def post_request(
        self, url: str, data: dict, headers: dict
    ) -> AsyncIterable[Activity]:
        """Send a POST request to the specified URL with the given data and headers.

        :param url: The URL to which the POST request is sent.
        :param data: The data to be sent in the POST request body.
        :param headers: The headers to be included in the POST request.
        :return: An asynchronous iterable of Activity objects received in the response.
        """

        async with aiohttp.ClientSession(
            **self.settings.client_session_settings
        ) as session:
            async with session.post(url, json=data, headers=headers) as response:

                if response.status != 200:
                    # self.logger(f"Error sending request: {response.status}")
                    raise aiohttp.ClientError(
                        f"Error sending request: {response.status}"
                    )

                # Set conversation ID from response header when status is 200
                conversation_id_header = response.headers.get("x-ms-conversationid")
                if conversation_id_header:
                    self._current_conversation_id = conversation_id_header

                event_type = None
                async for line in response.content:
                    if line.startswith(b"event:"):
                        event_type = line[6:].decode("utf-8").strip()
                    if line.startswith(b"data:") and event_type == "activity":
                        activity_data = line[5:].decode("utf-8").strip()
                        activity = Activity.model_validate_json(activity_data)

                        if activity.type == ActivityTypes.message:
                            self._current_conversation_id = activity.conversation.id

                        yield activity

    async def start_conversation(
        self, emit_start_conversation_event: bool = True
    ) -> AsyncIterable[Activity]:
        """Start a new conversation and optionally emit a start conversation event.

        :param emit_start_conversation_event: A boolean flag indicating whether to emit a start conversation event.
        :return: An asynchronous iterable of Activity objects received in the response.
        """

        url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
            settings=self.settings
        )
        data = {"emitStartConversationEvent": emit_start_conversation_event}
        headers = {
            "Content-Type": self.APPLICATION_JSON_TYPE,
            "Authorization": f"Bearer {self._token}",
            "Accept": self.EVENT_STREAM_TYPE,
        }

        async for activity in self.post_request(url, data, headers):
            yield activity

    async def ask_question(
        self, question: str, conversation_id: Optional[str] = None
    ) -> AsyncIterable[Activity]:
        """Ask a question in the specified conversation.

        :param question: The question to be asked.
        :param conversation_id: The ID of the conversation in which the question is asked. If not provided, the current conversation ID is used.
        :return: An asynchronous iterable of Activity objects received in the response.
        """

        activity = Activity(
            type="message",
            text=question,
            conversation=ConversationAccount(
                id=conversation_id or self._current_conversation_id
            ),
        )

        async for activity in self.ask_question_with_activity(activity):
            yield activity

    async def ask_question_with_activity(
        self, activity: Activity
    ) -> AsyncIterable[Activity]:
        """Ask a question using an Activity object.

        :param activity: The Activity object representing the question to be asked.
        :return: An asynchronous iterable of Activity objects received in the response.
        """

        if not activity:
            raise ValueError(
                "CopilotClient.ask_question_with_activity: Activity cannot be None"
            )

        local_conversation_id = (
            activity.conversation.id or self._current_conversation_id
        )

        url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
            settings=self.settings, conversation_id=local_conversation_id
        )
        data = ExecuteTurnRequest(activity=activity).model_dump(
            mode="json", by_alias=True, exclude_unset=True
        )
        headers = {
            "Content-Type": self.APPLICATION_JSON_TYPE,
            "Authorization": f"Bearer {self._token}",
            "Accept": self.EVENT_STREAM_TYPE,
        }

        async for activity in self.post_request(url, data, headers):
            yield activity
