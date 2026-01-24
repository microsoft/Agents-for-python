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

from .send import Sender
from .receive import ResponseReceiver
from .sr_node import SRNode

class AgentClient:
    """Client for sending activities to an agent and collecting responses."""
    
    def __init__(
        self,
        sender: Sender,
        receiver: ResponseReceiver,
        activity_template: ModelTemplate[Activity] | None = None
    ) -> None:
        """Initializes the AgentClient with a sender, collector, and optional activity template.
        
        :param sender: The SenderClient to send activities.
        :param collector: The ResponseCollector to collect responses.
        :param activity_template: Optional ActivityTemplate for creating activities.
        """
        self._sender = sender
        self._receiver = receiver
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
    
    async def _send(
        self,
        activity: Activity
    ) -> SRNode:
        """Sends an activity using the sender and returns the SRNode response.
        
        :param activity: The Activity to send.
        :return: The SRNode response from the sender.
        """
        sr_node = await self._sender.send(activity)
        self._receiver.add(sr_node)
        return sr_node
    
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

        sr_node = await self._send(activity)

        if max(0.0, wait) != 0.0: # ignore negative waits, I guess
            await asyncio.sleep(wait)
            new_activities = self._receiver.get_new()
            return sr_node.received + new_activities

        return sr_node.received
    
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
        
        sr_node = await self._sender._send(activity)
        if not sr_node.invoke_response:
            if sr_node.exception:
                raise sr_node.exception
            raise RuntimeError("AgentClient.invoke(): No InvokeResponse received")
        
        return sr_node.invoke_response
    
    def get_all(self) -> list[Activity]:
        """Gets all received activities from the receiver.
        
        :return: A list of all received Activities.
        """
        return self._receiver.get_all()