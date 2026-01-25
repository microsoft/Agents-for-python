# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from aiohttp import ClientSession
from microsoft_agents.activity import Activity

from .exchange import Exchange 
from .transcript import Transcript

class Sender(ABC):
    """Client for sending activities to an agent endpoint."""

    def __init__(self, transcript: Transcript | None = None):
        self._transcript: Transcript = transcript or Transcript()

    @property
    def transcript(self) -> Transcript:
        """The Transcript that collects sent Exchanges."""
        return self._transcript

    @abstractmethod
    async def send(self, activity: Activity) -> Exchange:
        """Send an activity and return the Exchange containing the response."""
        ...

class AiohttpSender(Sender):
    
    def __init__(self, session: ClientSession, transcript: Transcript | None = None):
        super().__init__(transcript)
        self._session = session

    async def send(self, activity: Activity) -> Exchange:
        """Send an activity and return the Exchange containing the response.
        
        :param activity: The Activity to send.
        :return: An Exchange object containing the response.
        """
        
        exchange: Exchange
        try:
            async with self._session.post(
                "api/messages",
                json=activity.model_dump(
                    by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
                )
            ) as response:
                exchange = await Exchange.from_request(activity, response)
        
        except Exception as e:
            exchange = await Exchange.from_request(activity, e)
        
        self._transcript.record(exchange)
        return exchange