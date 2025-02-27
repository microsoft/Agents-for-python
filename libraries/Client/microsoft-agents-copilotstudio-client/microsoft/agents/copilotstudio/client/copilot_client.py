import aiohttp
from typing import AsyncIterable, Callable, Optional

from microsoft.agents.core.models import Activity, ConversationAccount

from .connection_settings import ConnectionSettings
from .execute_turn_request import ExecuteTurnRequest


class CopilotClient:
    def __init__(
        self,
        settings: ConnectionSettings,
        logger: Callable,
        token_provider_function: Optional[Callable[[str], str]] = None,
    ):
        self.settings = settings
        self.logger = logger
        self.token_provider_function = token_provider_function
        self.conversation_id = ""

    async def post_request(
        self, url: str, data: dict, headers: dict
    ) -> AsyncIterable[Activity]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    self.logger(f"Error sending request: {response.status}")
                    raise aiohttp.ClientError(
                        f"Error sending request: {response.status}"
                    )
                event_type = None
                async for line in response.content:
                    if line.startswith(b"event:"):
                        event_type = line[6:].decode("utf-8").strip()
                    if line.startswith(b"data:") and event_type == "activity":
                        activity_data = line[5:].decode("utf-8").strip()
                        activity = Activity.from_json(activity_data)
                        yield activity

    async def start_conversation(
        self, emit_start_conversation_event: bool = True
    ) -> AsyncIterable[Activity]:
        url = self.settings.get_connection_url()
        data = {"EmitStartConversationEvent": emit_start_conversation_event}
        headers = {"Content-Type": "application/json"}
        if self.token_provider_function:
            token = await self.token_provider_function(url)
            headers["Authorization"] = f"Bearer {token}"
        return self.post_request(url, data, headers)

    async def ask_question(
        self, question: str, conversation_id: Optional[str] = None
    ) -> AsyncIterable[Activity]:
        activity = Activity(
            type="message",
            text=question,
            conversation=ConversationAccount(id=conversation_id),
        )
        return self.ask_question_with_activity(activity)

    async def ask_question_with_activity(
        self, activity: Activity
    ) -> AsyncIterable[Activity]:
        url = self.settings.get_connection_url(self.conversation_id)
        data = ExecuteTurnRequest(activity=activity).to_json()
        headers = {"Content-Type": "application/json"}
        if self.token_provider_function:
            token = await self.token_provider_function(url)
            headers["Authorization"] = f"Bearer {token}"
        return self.post_request(url, data, headers)
