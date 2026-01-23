# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
from typing import cast

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)
from microsoft_agents.testing.utils import ActivityTemplate

from .response_collector import ResponseCollector
from .sender_client import SenderClient

class AgentClient:
    """Client for sending activities to an agent and collecting responses."""
    
    def __init__(self,
                 sender: SenderClient,
                 collector: ResponseCollector,
                 activity_template: ActivityTemplate | None = None) -> None:
        """Initializes the AgentClient with a sender, collector, and optional activity template.
        
        :param sender: The SenderClient to send activities.
        :param collector: The ResponseCollector to collect responses.
        :param activity_template: Optional ActivityTemplate for creating activities.
        """
        
        if not sender or not collector:
            raise ValueError("Sender and collector must be provided.")
        
        self._sender: SenderClient = sender
        self._collector: ResponseCollector = collector

        self._activity_template = activity_template or ActivityTemplate()

    @property
    def activity_template(self) -> ActivityTemplate:
        """Gets the current ActivityTemplate."""
        return self._activity_template
    
    @activity_template.setter
    def activity_template(self, activity_template: ActivityTemplate) -> None:
        """Sets a new ActivityTemplate."""
        self._activity_template = activity_template

    def activity(self, activity_or_str: Activity | str) -> Activity:
        """Creates an Activity using the activity template.
        
        :param activity_or_str: An Activity or string to base the new Activity on.
        :return: A new Activity instance.
        """
        if isinstance(activity_or_str, Activity):
            base = cast(Activity, activity_or_str)
        else:
            base = Activity(
                type=ActivityTypes.message,
                text=activity_or_str
            )

        return self._activity_template.create(base)

    def get_activities(self) -> list[Activity]:
        """Returns all collected activities.
        
        :return: A list of collected Activities.
        """
        return self._collector.get_activities()

    def get_invoke_responses(self) -> list[InvokeResponse]:
        """Returns all collected invoke responses.
        
        :return: A list of collected InvokeResponses.
        """
        return self._collector.get_invoke_responses()
    
    async def send(self,
                   activity_or_text: Activity | str,
                   response_wait: float = 0.0,
                   ) -> list[Activity | InvokeResponse]:
        """Sends an activity and collects responses.
        
        :param activity_or_text: An Activity or string to send.
        :param response_wait: Time in seconds to wait for additional responses after sending.
        :return: A list of received Activities and InvokeResponses.
        """

        self._collector.pop()
        received_activities = []

        activity_to_send = self.activity(activity_or_text)

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

        if response_wait != 0.0:
            await asyncio.sleep(response_wait)

        post_post_activities = self._collector.pop()

        return received_activities + post_post_activities
    
    async def send_expect_replies(
        self,
        activity_or_text: Activity | str,
    ) -> list[Activity]:
        """Sends an activity with expect_replies delivery mode and collects replies.
        
        :param activity_or_text: An Activity or string to send.
        :return: A list of reply Activities.
        """
        
        activity_to_send = self.activity(activity_or_text)
        activity_to_send.delivery_mode = DeliveryModes.expect_replies

        activities = await self._sender.send_expect_replies(activity_to_send)
        for act in activities:
            self._collector.add(act)

        return activities
    
    async def wait_for_responses(self, duration: float = 0.0) -> list[Activity]:
        """Waits for a specified duration and returns new activities collected.

        :param duration: Time in seconds to wait for new activities.
        :return: A list of new Activities collected during the wait.
        """

        if duration < 0.0:
            raise ValueError("Duration must be non-negative.")
        await asyncio.sleep(duration)

        return self._collector.pop()