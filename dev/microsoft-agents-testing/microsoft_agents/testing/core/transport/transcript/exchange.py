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
        if self.request_at is not None and self.response_at is not None:
            return self.response_at - self.request_at
        return None
    
    @property
    def latency_ms(self) -> float | None:
        delta = self.latency
        if delta is not None:
            return delta.total_seconds() * 1000.0
        return None
    
    @staticmethod
    def is_allowed_exception(exception: Exception) -> bool:
        return isinstance(exception, (aiohttp.ClientTimeout, aiohttp.ClientConnectionError))
    
    @staticmethod
    async def from_request(
        request_activity: Activity,
        response_or_exception: Exception | ResponseT,
        **kwargs
    ) -> Exchange:
        
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

            body = await response.text()

            activities = []
            invoke_response = None

            if request_activity.delivery_mode == DeliveryModes.expect_replies:
                body_json = json.loads(body)
                activities = [ Activity.model_validate(activity) for activity in body_json ]
                
            elif request_activity.type == ActivityTypes.invoke:
                body_json = json.loads(body)
                invoke_response = InvokeResponse.model_validate({"status": response.status, "body": body_json})
            # else:
            #     content = await response.text()

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