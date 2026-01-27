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
from microsoft_agents.testing.utils import ActivityTemplate

from .exchange import (
    Transcript,
    Sender,
    Exchange
)

class AgentClient:
    """Client for sending activities to an agent and collecting responses."""
    
    def __init__(
        self,
        sender: Sender,
        transcript: Transcript | None = None,
        activity_template: ActivityTemplate | None = None
    ) -> None:
        """Initializes the AgentClient with a sender, transcript, and optional activity template.
        
        :param sender: The Sender to send activities.
        :param transcript: The Transcript to collect exchanges.
        :param activity_template: Optional ActivityTemplate for creating activities.
        """
        
        self._sender = sender

        transcript = transcript or Transcript()
        self._transcript = transcript

        self._template = activity_template or ActivityTemplate()
        
    @property
    def template(self) -> ActivityTemplate:
        """Gets the current ActivityTemplate."""
        return self._template
    
    @template.setter
    def template(self, activity_template: ActivityTemplate) -> None:
        """Sets a new ActivityTemplate."""
        self._template = activity_template

    @property
    def transcript(self) -> Transcript:
        """Get the Transcript associated with this AgentClient."""
        return self._transcript

    def _build_activity(self, base: Activity | str) -> Activity:
        """Build an activity from string or Activity, applying template."""
        if isinstance(base, str):
            base = Activity(type=ActivityTypes.message, text=base)
        return self._template.create(base)

    
    async def ex_send(
        self,
        activity_or_text: Activity | str,
        *,
        wait: float = 0.0,
        **kwargs,
    ) -> list[Exchange]:
        """Sends an activity and collects responses.
        
        :param activity_or_text: An Activity or string to send.
        :param wait: Time in seconds to wait for additional responses after sending.
        :param kwargs: Additional arguments to pass to the sender.
        :return: A list of received Exchanges.
        """

        activity = self._build_activity(activity_or_text)

        self._transcript.get_new()

        exchange = await self._sender.send(activity, transcript=self._transcript, **kwargs)

        if max(0.0, wait) != 0.0: # ignore negative waits, I guess
            await asyncio.sleep(wait)
            return [exchange] + self._transcript.get_new()

        return [exchange]
    
    async def send(
        self,
        activity_or_text: Activity | str,
        *,
        wait: float = 0.0,
        **kwargs,
    ) -> list[Activity]:
        """Sends an activity and collects reply activities.
        
        :param activity_or_text: An Activity or string to send.
        :param wait: Time in seconds to wait for additional responses after sending.
        :param kwargs: Additional arguments to pass to the sender.
        :return: A list of reply Activities.
        """
        exchanges = await self.ex_send(activity_or_text, wait=wait, **kwargs)
        lst = []
        for exchange in exchanges:
            lst.extend(exchange.responses)
        return lst
    
    async def ex_send_expect_replies(
        self,
        activity_or_text: Activity | str,
        **kwargs,
    ) -> list[Exchange]:
        """Sends an activity with expect_replies delivery mode and collects replies.
        
        :param activity_or_text: An Activity or string to send.
        :param kwargs: Additional arguments to pass to the sender.
        :return: A list of reply Activities.
        """
        activity = self._build_activity(activity_or_text)
        activity.delivery_mode = DeliveryModes.expect_replies
        return await self.ex_send(activity, wait=0.0, **kwargs)
    
    async def send_expect_replies(
        self,
        activity_or_text: Activity | str,
        **kwargs,
    ) -> list[Activity]:
        """Sends an activity with expect_replies delivery mode and collects replies.
        
        :param activity_or_text: An Activity or string to send.
        :param kwargs: Additional arguments to pass to the sender.
        :return: A list of reply Activities.
        """
        exchanges = await self.ex_send_expect_replies(activity_or_text, **kwargs)
        lst = []
        for exchange in exchanges:
            lst.extend(exchange.responses)
        return lst
    
    async def ex_invoke(
        self, 
        activity: Activity,
        **kwargs,
    ) -> Exchange:
        """Sends an invoke activity and returns the InvokeResponse.
        
        :param activity: The invoke Activity to send.
        :param kwargs: Additional arguments to pass to the sender.
        :return: The InvokeResponse received.
        """
        activity = self._build_activity(activity)
        if activity.type != ActivityTypes.invoke:
            raise ValueError("AgentClient.invoke(): Activity type must be 'invoke'")
        
        exchanges = await self._sender.send(activity, transcript=self._transcript, **kwargs)
        assert len(exchanges) == 1
        exchange = exchanges[0]
        
        if not exchange.invoke_response:
            # in order to not violate the contract,
            # we raise the exception if there is no InvokeResponse
            if not exchange.error:
                raise RuntimeError("AgentClient.invoke(): No InvokeResponse received")
            raise Exception(exchange.error)
        
        return exchange
    
    async def invoke(
        self,
        activity: Activity,
        **kwargs,
    ) -> InvokeResponse:
        """Sends an invoke activity and returns the InvokeResponse.
        
        :param activity: The invoke Activity to send.
        :param kwargs: Additional arguments to pass to the sender.
        :return: The InvokeResponse received.
        """
        exchange = await self.ex_invoke(activity, **kwargs)
        return exchange.invoke_response
    
    def ex_get_all(self) -> list[Activity]:
        """Gets all received activities from the transcript.
        
        :return: A list of all received Activities.
        """
        return self._transcript.get_all()
    
    def get_all(self) -> list[Activity]:
        """Gets all received activities from the transcript.
        
        :return: A list of all received Activities.
        """
        lst = []
        for exchange in self._transcript.get_all():
            lst.extend(exchange.responses)
        return lst
    
    def ex_get_new(self) -> list[Activity]:
        """Gets new received activities from the transcript since the last call.
        
        :return: A list of new received Activities.
        """
        return self._transcript.get_new()
    
    def get_new(self) -> list[Activity]:
        """Gets new received activities from the transcript since the last call.
        
        :return: A list of new received Activities.
        """
        lst = []
        for exchange in self._transcript.get_new():
            lst.extend(exchange.responses)
        return lst
    
    def child(self) -> AgentClient:
        return AgentClient(
            self._sender,
            transcript=self._transcript.child(),
            activity_template=self._template)