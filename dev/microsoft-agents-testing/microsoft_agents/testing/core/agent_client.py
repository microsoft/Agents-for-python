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

from .fluent import (
    ActivityTemplate,
    Expect,
    Select,
)
from .transport import (
    Transcript,
    Exchange,
    Sender
)

def activities_from_ex(exchanges: list[Exchange]) -> list[Activity]:
    """Extracts all response activities from a list of exchanges."""
    activities: list[Activity] = []
    for exchange in exchanges:
        activities.extend(exchange.responses)
    return activities

class AgentClient:
    """Client for sending activities to an agent and collecting responses."""
    
    def __init__(
        self,
        sender: Sender,
        transcript: Transcript | None = None,
        template: ActivityTemplate | None = None
    ) -> None:
        """Initializes the AgentClient with a sender, transcript, and optional activity template.
        
        :param sender: The Sender to send activities.
        :param transcript: The Transcript to collect exchanges.
        :param activity_template: Optional ActivityTemplate for creating activities.
        """
        
        self._sender = sender

        transcript = transcript or Transcript()
        self._transcript = transcript

        self._template = template or ActivityTemplate()
        
    @property
    def template(self) -> ActivityTemplate:
        """Gets the current ActivityTemplate."""
        return self._template
    
    @template.setter
    def template(self, template: ActivityTemplate) -> None:
        """Sets a new ActivityTemplate."""
        self._template = template

    @property
    def transcript(self) -> Transcript:
        """Get the Transcript associated with this AgentClient."""
        return self._transcript
    
    ###
    ### Transcript collection/manipulation
    ###

    def _ex_collect(self, history: bool = True) -> list[Exchange]:
        if history:
            return self._transcript.get_root().history()
        else:
            return self._transcript.history()
        
    def _collect(self, history: bool = True) -> list[Activity]:
        ex = self._ex_collect(history)
        return activities_from_ex(ex)
    
    def ex_recent(self) -> list[Exchange]:
        """Gets the most recent exchanges from the transcript."""
        return self._ex_collect()
    
    def recent(self) -> list[Activity]:
        """Gets the most recent activities from the transcript."""
        return self._collect()
    
    def ex_history(self) -> list[Exchange]:
        """Gets the full exchange history from the transcript."""
        return self._ex_collect(history=True)
    
    def history(self) -> list[Activity]:
        """Gets the full activity history from the transcript."""
        return self._collect(history=True)
    
    def clear(self) -> None:
        """Clears the transcript."""
        self._transcript.clear()
    
    ###
    ### Utilities
    ###

    def ex_select(self, history: bool = False) -> Select:
        return Select(self._ex_collect(history=history))

    def select(self, recent: bool = False) -> Select:
        """"""
        return Select(self._collect(history=recent))
    
    def expect_ex(self, history: bool = True) -> Expect:
        """"""
        return Expect(self._ex_collect(history=history))

    def expect(self, history: bool = True) -> Expect:
        return Expect(self._collect(history=history))
        
    ###
    ### Sending API
    ###
    
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


        exchange = await self._sender.send(activity, transcript=self._transcript, **kwargs)

        if max(0.0, wait) != 0.0: # ignore negative waits, I guess
            await asyncio.sleep(wait)
            return self.ex_recent()

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
        return activities_from_ex(
            await self.ex_send(activity_or_text, wait=wait, **kwargs)
        )
    
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
        return activities_from_ex(
            await self.ex_send_expect_replies(activity_or_text, **kwargs)
        )
    
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
        
        exchange = await self._sender.send(activity, transcript=self._transcript, **kwargs)
        
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
    ) -> InvokeResponse | None:
        """Sends an invoke activity and returns the InvokeResponse.
        
        :param activity: The invoke Activity to send.
        :param kwargs: Additional arguments to pass to the sender.
        :return: The InvokeResponse received.
        """
        exchange = await self.ex_invoke(activity, **kwargs)
        return exchange.invoke_response
    
    def child(self) -> AgentClient:
        return AgentClient(
            self._sender,
            transcript=self._transcript.child(),
            template=self._template)