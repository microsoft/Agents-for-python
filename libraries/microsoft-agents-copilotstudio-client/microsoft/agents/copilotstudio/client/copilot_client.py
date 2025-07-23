import aiohttp
from typing import AsyncIterable, Callable, Optional

from microsoft.agents.activity import Activity, ActivityTypes, ConversationAccount

from .connection_settings import ConnectionSettings
from .execute_turn_request import ExecuteTurnRequest
from .power_platform_environment import PowerPlatformEnvironment


class CopilotClient:
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
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    # self.logger(f"Error sending request: {response.status}")
                    raise aiohttp.ClientError(
                        f"Error sending request: {response.status}"
                    )
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
