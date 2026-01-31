# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timezone

from aiohttp import ClientSession

from microsoft_agents.activity import Activity

from .sender import Sender
from .transcript import Transcript, Exchange

class AiohttpSender(Sender):
    
    def __init__(self, session: ClientSession):
        self._session = session

    async def send(self, activity: Activity, transcript: Transcript | None = None, **kwargs) -> Exchange:
        """Send an activity and return the Exchange containing the response.
        
        :param activity: The Activity to send.
        :param transcript: Optional Transcript to record the exchange.
        :param timeout: Optional timeout for the request.
        :return: An Exchange object containing the response.
        """
        
        exchange: Exchange
        response_or_exception = None
        request_at = datetime.now(timezone.utc)
        try:
            async with self._session.post(
                "api/messages",
                json=activity.model_dump(
                    by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
                ),
                **kwargs
            ) as response:
                response_at = datetime.now(timezone.utc)
                response_or_exception = response

                exchange = await Exchange.from_request(
                    request_activity=activity,
                    response_or_exception=response_or_exception,
                    request_at=request_at,
                    response_at=response_at,
                    **kwargs
                )
                
        
        except Exception as e:
            response_at = datetime.now(timezone.utc)
            response_or_exception = e 

            exchange = await Exchange.from_request(
                request_activity=activity,
                response_or_exception=response_or_exception,
                request_at=request_at,
                response_at=response_at,
                **kwargs
            )
        
        if transcript:
            transcript.record(exchange)
        return exchange