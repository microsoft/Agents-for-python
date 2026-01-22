from __future__ import annotations

import asyncio
from contextlib import contextmanager
from collections.abc import AsyncIterator
from typing import Callable, cast, Awaitable

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)
from microsoft_agents.testing.utils import ActivityTemplate

from .agent_client_config import AgentClientConfig
from .response_collector import ResponseCollector
from .sender_client import SenderClient

class AgentClient(ResponseCollector):
    
    def __init__(self,
                 sender: SenderClient,
                 collector: ResponseCollector,
                 agent_client_config: AgentClientConfig | None = None):
        
        if not sender or not collector:
            raise ValueError("Sender and collector must be provided.")
        
        self._sender: SenderClient = sender
        self._collector: ResponseCollector = collector
        self._activity_template = agent_client_config.activity_template

        self._config = agent_client_config or AgentClientConfig()

    @property
    def activity_template(self) -> ActivityTemplate:
        return self._activity_template
    
    @activity_template.setter
    def set_activity_template(self, activity_template: ActivityTemplate) -> None:
        self._activity_template = activity_template

    def _create_activity(self, activity_or_str: Activity | str) -> Activity:
        if isinstance(activity_or_str, Activity):
            base = cast(Activity, activity_or_str)
        else:
            base = Activity(
                type=ActivityTypes.message,
                text=activity_or_str
            )

        return self._activity_template.create(base)

    def get_activities(self) -> list[Activity]:
        return self._collector.get_activities()

    def get_invoke_responses(self) -> list[InvokeResponse]:
        return self._collector.get_invoke_responses()
    
    def _fork(self, agent_client_config: AgentClientConfig | None = None) -> AgentClient:
        client = AgentClient(
            self._sender,
            self._collector,
            agent_client_config or self._config
        )
        return client

    async def conversation(self) -> AgentClient:
        pass
    
    async def send(self,
                   activity_or_text: Activity | str,
                   wait_for_responses: float = 0.0,
                   ) -> list[Activity | InvokeResponse]:

        self._collector.pop()
    
        received_activities = []

        activity_to_send = self._create_activity(activity_or_text)

        if activity_to_send.type == ActivityTypes.invoke:
            invoke_response = await self._sender.send_invoke(activity_to_send)
            self._collector.add(invoke_response)
        elif activity_to_send.delivery_mode == DeliveryModes.expect_replies:
            replies = await self._sender.send_expect_replies(activity_to_send)
            for reply in replies:
                self._collector.add(reply)
                received_activities.append(reply)
        else:
            await self._sender.send(activity_to_send)

        if wait_for_responses != 0.0:
            await asyncio.sleep(wait_for_responses)

        post_post_activities = self._collector.pop()

        return received_activities + post_post_activities
    
    async def send_expect_replies(
        self,
        activity_or_text: Activity | str,
    ) -> list[Activity]:
        
        activity_to_send = self._create_activity(activity_or_text)
        activity_to_send.delivery_mode = DeliveryModes.expect_replies

        activities = await self._sender.send_expect_replies(activity_to_send)
        for act in activities:
            self._collector.add(act)

        return activities
    
    async def wait_for_responses(self, duration: float = 0.0) -> list[Activity]:
        if duration < 0.0:
            raise ValueError("Duration must be non-negative.")
        await asyncio.sleep(duration)

        return self._collector.pop()