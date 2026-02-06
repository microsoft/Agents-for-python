# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Exchange - A single request-response interaction with an agent.

Captures the complete lifecycle of sending an activity and receiving
responses, including timing, status codes, and any errors.
"""

from __future__ import annotations

import json
from typing import cast, TypeVar
from datetime import datetime

import aiohttp
from pydantic import BaseModel, Field

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

# supported Response types, currently only aiohttp.ClientResponse
ResponseT = TypeVar("ResponseT", bound=aiohttp.ClientResponse)

class Exchange(BaseModel):
    """A complete send-receive exchange with an agent.
    
    Captures the outgoing activity, the HTTP response, and any
    activities received (inline replies or async callbacks).
    """
    # The activity that was sent
    request: Activity | None = None
    request_at: datetime | None = None
    
    # HTTP response metadata
    status_code: int | None = None
    body: str | None = None
    invoke_response: InvokeResponse | None = None
    
    # Error if the request failed
    error: str | None = None
    
    # Activities received (from expect_replies or callbacks)
    responses: list[Activity] = Field(default_factory=list)
    response_at: datetime | None = None
    
    @property
    def latency(self) -> datetime | None:
        """Calculate the time delta between request and response.

        :return: A timedelta object, or None if either timestamp is missing.
        """
        if self.request_at is not None and self.response_at is not None:
            return self.response_at - self.request_at
        return None
    
    @property
    def latency_ms(self) -> float | None:
        """Calculate the latency in milliseconds.

        :return: Latency in milliseconds, or None if timestamps are missing.
        """
        delta = self.latency
        if delta is not None:
            return delta.total_seconds() * 1000.0
        return None
    
    @staticmethod
    def is_allowed_exception(exception: Exception) -> bool:
        """Check if an exception is a recoverable transport error.

        Timeout and connection errors are considered recoverable and
        will be captured in the Exchange rather than re-raised.

        :param exception: The exception to check.
        :return: True if the exception is a known recoverable error.
        """
        return isinstance(exception, (aiohttp.ClientTimeout, aiohttp.ClientConnectionError))
    
    @staticmethod
    async def from_request(
        request_activity: Activity,
        response_or_exception: Exception | ResponseT,
        **kwargs
    ) -> Exchange:
        """Create an Exchange from a request activity and its outcome.

        Handles three response types:
        - Exception: Wraps recoverable errors; re-raises unexpected ones.
        - aiohttp.ClientResponse: Parses the response based on the
          activity's delivery mode (expect_replies, invoke, stream, or default).

        :param request_activity: The Activity that was sent.
        :param response_or_exception: The HTTP response or exception.
        :param kwargs: Additional fields forwarded to the Exchange constructor
                       (e.g., request_at, response_at).
        :return: A populated Exchange instance.
        :raises: Re-raises exceptions that are not in the allowed list.
        """
        
        if isinstance(response_or_exception, Exception):
            if not Exchange.is_allowed_exception(response_or_exception):
                raise response_or_exception
            
            return Exchange(
                request=request_activity,
                error=str(response_or_exception),
                **kwargs,
            )
        
        if isinstance(response_or_exception, aiohttp.ClientResponse):
            
            response = cast(aiohttp.ClientResponse, response_or_exception)

            body: str | None = None
            activities: list[Activity] = []
            invoke_response: InvokeResponse | None = None

            # Parse the response body based on the request's delivery mode
            if request_activity.delivery_mode == DeliveryModes.expect_replies:
                body = await response.text()
                activity_list = json.loads(body)["activities"]
                activities = [ Activity.model_validate(activity) for activity in activity_list ]
                
            elif request_activity.type == ActivityTypes.invoke:
                body = await response.text()
                body_json = json.loads(body)
                invoke_response = InvokeResponse.model_validate({"status": response.status, "body": body_json})

            elif request_activity.delivery_mode == DeliveryModes.stream:
                # Parse Server-Sent Events (SSE) stream for activity events
                event_type = None
                body = ""
                async for line in response.content:
                    body += line.decode("utf-8")
                    if line.startswith(b"event:"):
                        event_type = line[6:].decode("utf-8").strip()
                    if line.startswith(b"data:") and event_type == "activity":
                        activity_data = line[5:].decode("utf-8").strip()
                        activities.append(Activity.model_validate_json(activity_data))
            else:
                body = await response.text()

            return Exchange(
                request=request_activity,
                status_code=response.status,
                body=body,
                responses=activities,
                invoke_response=invoke_response,
                **kwargs
            )
            
        else:
            raise ValueError("response_or_exception must be an Exception or aiohttp.ClientResponse")