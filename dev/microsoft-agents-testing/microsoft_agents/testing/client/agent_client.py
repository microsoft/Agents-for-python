# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)
from microsoft_agents.testing.utils import ModelTemplate

from .exchange import Sender, Transcript

class AgentClient:
    """Client for sending activities to an agent and collecting responses."""
    
    def __init__(
        self,
        sender: Sender,
        transcript: Transcript,
        activity_template: ModelTemplate[Activity] | None = None
    ) -> None:
        """Initializes the AgentClient with a sender, transcript, and optional activity template.
        
        :param sender: The Sender to send activities.
        :param transcript: The Transcript to collect exchanges.
        :param activity_template: Optional ModelTemplate for creating activities.
        """
        self._sender = sender
        self._transcript = transcript
        self._template = activity_template or ModelTemplate[Activity]()
        
    @property
    def template(self) -> ModelTemplate[Activity]:
        """Gets the current ActivityTemplate."""
        return self._template
    
    @template.setter
    def template(self, activity_template: ModelTemplate[Activity]) -> None:
        """Sets a new ActivityTemplate."""
        self._template = activity_template

    def _build_activity(self, base: Activity | str) -> Activity:
        """Build an activity from string or Activity, applying template."""
        if isinstance(base, str):
            base = Activity(type=ActivityTypes.message, text=base)
        return self._template.create(base)
    
    async def send(
        self,
        activity_or_text: Activity | str,
        wait: float = 0.0,
    ) -> list[Activity]:
        """Sends an activity and collects responses.
        
        :param activity_or_text: An Activity or string to send.
        :param wait: Time in seconds to wait for additional responses after sending.
        :return: A list of received Activities.
        """

        activity = self._build_activity(activity_or_text)

        self._receiver.get_new()

        exchange = await self._sender.send(activity)

        if max(0.0, wait) != 0.0: # ignore negative waits, I guess
            await asyncio.sleep(wait)
            new_activities = self._receiver.get_new()
            return exchange.responses + new_activities

        return exchange.responses
    
    async def send_expect_replies(
        self,
        activity_or_text: Activity | str,
    ) -> list[Activity]:
        """Sends an activity with expect_replies delivery mode and collects replies.
        
        :param activity_or_text: An Activity or string to send.
        :return: A list of reply Activities.
        """
        activity = self._build_activity(activity_or_text)
        activity.delivery_mode = DeliveryModes.expect_replies
        return await self.send(activity)
    
    async def invoke(
        self, 
        activity: Activity
    ) -> InvokeResponse:
        """Sends an invoke activity and returns the InvokeResponse.
        
        :param activity: The invoke Activity to send.
        :return: The InvokeResponse received.
        """
        activity = self._build_activity(activity)
        if activity.type != ActivityTypes.invoke:
            raise ValueError("AgentClient.invoke(): Activity type must be 'invoke'")
        
        exchange = await self._sender.send(activity)
        
        if not exchange.invoke_response:
            # in order to not violate the contract,
            # we raise the exception if there is no InvokeResponse
            if not exchange.exception:
                raise RuntimeError("AgentClient.invoke(): No InvokeResponse received")
            raise exchange.exception
        
        return exchange.invoke_response
    
    def get_all(self) -> list[Activity]:
        """Gets all received activities from the receiver.
        
        :return: A list of all received Activities.
        """
        lst = []
        for exchange in self._transcript.get_all():
            lst.extend(exchange.responses)
        return lst
    
    def get_new(self) -> list[Activity]:
        """Gets new received activities from the receiver since the last call.
        
        :return: A list of new received Activities.
        """
        lst = []
        for exchange in self._transcript.get_new():
            lst.extend(exchange.responses)
        return lst