# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import aiohttp
import logging
from typing import AsyncIterable, Callable, Optional

from microsoft_agents.activity import Activity, ActivityTypes, ConversationAccount

from .connection_settings import ConnectionSettings
from .execute_turn_request import ExecuteTurnRequest
from .power_platform_environment import PowerPlatformEnvironment
from .start_request import StartRequest
from .subscribe_event import SubscribeEvent
from .user_agent_helper import UserAgentHelper


class CopilotClient:
    """A client for interacting with the Copilot service."""

    EVENT_STREAM_TYPE = "text/event-stream"
    APPLICATION_JSON_TYPE = "application/json"
    EXPERIMENTAL_URL_HEADER_KEY = "x-ms-d2e-experimental"

    _current_conversation_id = ""

    def __init__(
        self,
        settings: ConnectionSettings,
        token: str,
    ):
        self.settings = settings
        self._token = token
        self._logger = logging.getLogger(__name__)
        self.conversation_id = ""
        self._island_experimental_url = ""

    async def post_request(
        self, url: str, data: dict, headers: dict
    ) -> AsyncIterable[Activity]:
        """Send a POST request to the specified URL with the given data and headers.

        :param url: The URL to which the POST request is sent.
        :param data: The data to be sent in the POST request body.
        :param headers: The headers to be included in the POST request.
        :return: An asynchronous iterable of Activity objects received in the response.
        """
        # Add User-Agent header
        headers["User-Agent"] = UserAgentHelper.get_user_agent_header()

        # Log diagnostic information if enabled
        if self.settings.enable_diagnostics:
            self._logger.debug(f">>> SEND TO {url}")

        async with aiohttp.ClientSession(
            **self.settings.client_session_settings
        ) as session:
            async with session.post(url, json=data, headers=headers) as response:

                if response.status != 200:
                    self._logger.error(f"Error sending request: {response.status}")
                    raise aiohttp.ClientError(
                        f"Error sending request: {response.status}"
                    )

                # Log response headers if diagnostics enabled
                if self.settings.enable_diagnostics:
                    self._logger.debug("=" * 53)
                    for header_key, header_value in response.headers.items():
                        self._logger.debug(f"{header_key} = {header_value}")
                    self._logger.debug("=" * 53)

                # Capture experimental endpoint if enabled and not already using DirectConnect
                experimental_url = response.headers.get(
                    self.EXPERIMENTAL_URL_HEADER_KEY
                )
                if experimental_url:
                    if (
                        self.settings.use_experimental_endpoint
                        and not self.settings.direct_connect_url
                    ):
                        self._island_experimental_url = experimental_url
                        self.settings.direct_connect_url = self._island_experimental_url
                        self._logger.debug(
                            f"Island Experimental URL: {self._island_experimental_url}"
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

    async def start_conversation_with_request(
        self, start_request: StartRequest
    ) -> AsyncIterable[Activity]:
        """Start a new conversation with a StartRequest object.

        :param start_request: The StartRequest containing conversation parameters.
        :return: An asynchronous iterable of Activity objects received in the response.
        """

        url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
            settings=self.settings
        )
        data = start_request.model_dump(mode="json", by_alias=True, exclude_unset=True)
        headers = {
            "Content-Type": self.APPLICATION_JSON_TYPE,
            "Authorization": f"Bearer {self._token}",
            "Accept": self.EVENT_STREAM_TYPE,
        }

        async for activity in self.post_request(url, data, headers):
            yield activity

    async def send_activity(self, activity: Activity) -> AsyncIterable[Activity]:
        """Send an activity to the bot.

        This is an alias for ask_question_with_activity for consistency with the .NET implementation.

        :param activity: The Activity object to send.
        :return: An asynchronous iterable of Activity objects received in the response.
        """
        async for result_activity in self.ask_question_with_activity(activity):
            yield result_activity

    async def execute(
        self, conversation_id: str, activity: Activity
    ) -> AsyncIterable[Activity]:
        """Execute an activity with a specified conversation ID.

        :param conversation_id: The conversation ID.
        :param activity: The Activity object to execute.
        :return: An asynchronous iterable of Activity objects received in the response.
        """
        if not conversation_id:
            raise ValueError("CopilotClient.execute: conversation_id cannot be None")
        if not activity:
            raise ValueError("CopilotClient.execute: activity cannot be None")

        # Set the conversation ID on the activity
        if not activity.conversation:
            activity.conversation = ConversationAccount(id=conversation_id)
        else:
            activity.conversation.id = conversation_id

        async for result_activity in self.ask_question_with_activity(activity):
            yield result_activity

    async def subscribe(
        self, conversation_id: str, last_received_event_id: Optional[str] = None
    ) -> AsyncIterable[SubscribeEvent]:
        """Subscribe to conversation events.

        Note: This method is marked as obsolete in the .NET implementation and is for MSFT internal use only.

        :param conversation_id: The conversation ID to subscribe to.
        :param last_received_event_id: Optional last received event ID for resumption.
        :return: An asynchronous iterable of SubscribeEvent objects.
        """
        if not conversation_id:
            raise ValueError("CopilotClient.subscribe: conversation_id cannot be None")

        # Build the subscribe URL using the environment helper to ensure correct path and query handling
        url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
            settings=self.settings,
            conversation_id=conversation_id,
            create_subscribe_link=True,
        )
        headers = {
            "Content-Type": self.APPLICATION_JSON_TYPE,
            "Authorization": f"Bearer {self._token}",
            "Accept": self.EVENT_STREAM_TYPE,
        }

        # Add Last-Event-ID header if provided
        if last_received_event_id:
            headers["Last-Event-ID"] = last_received_event_id

        # Add User-Agent header
        headers["User-Agent"] = UserAgentHelper.get_user_agent_header()

        # Log diagnostic information if enabled
        if self.settings.enable_diagnostics:
            self._logger.debug(f">>> SEND TO {url}")

        async with aiohttp.ClientSession(
            **self.settings.client_session_settings
        ) as session:
            async with session.get(url, headers=headers) as response:

                if response.status != 200:
                    self._logger.error(
                        f"Error subscribing to conversation: {response.status}"
                    )
                    raise aiohttp.ClientError(
                        f"Error subscribing to conversation: {response.status}"
                    )

                # Log response headers if diagnostics enabled
                if self.settings.enable_diagnostics:
                    self._logger.debug("=" * 53)
                    for header_key, header_value in response.headers.items():
                        self._logger.debug(f"{header_key} = {header_value}")
                    self._logger.debug("=" * 53)

                event_id = None
                event_type = None
                async for line in response.content:
                    if line.startswith(b"id:"):
                        event_id = line[3:].decode("utf-8").strip()
                    elif line.startswith(b"event:"):
                        event_type = line[6:].decode("utf-8").strip()
                    elif line.startswith(b"data:") and event_type == "activity":
                        activity_data = line[5:].decode("utf-8").strip()
                        activity = Activity.model_validate_json(activity_data)
                        yield SubscribeEvent(activity=activity, event_id=event_id)

    @staticmethod
    def scope_from_settings(settings: ConnectionSettings) -> str:
        """Get the token audience scope from connection settings.

        :param settings: The ConnectionSettings object.
        :return: The token audience scope URL.
        """
        return PowerPlatformEnvironment.get_token_audience(settings=settings)

    @staticmethod
    def scope_from_cloud(cloud) -> str:
        """Get the token audience scope from PowerPlatformCloud.

        :param cloud: The PowerPlatformCloud value.
        :return: The token audience scope URL.
        """
        return PowerPlatformEnvironment.get_token_audience(cloud=cloud)
