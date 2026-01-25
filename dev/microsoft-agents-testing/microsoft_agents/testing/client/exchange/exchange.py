# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import json
from typing import cast

import aiohttp
from pydantic import BaseModel, Field

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

class Exchange(BaseModel):
    """A complete send-receive exchange with an agent.
    
    Captures the outgoing activity, the HTTP response, and any
    activities received (inline replies or async callbacks).
    """
    # The activity that was sent
    request: Activity | None = None
    
    # HTTP response metadata
    status_code: int | None = None
    response_body: str | None = None
    invoke_response: InvokeResponse | None = None
    
    # Error if the request failed
    error: Exception | None = None
    
    # Activities received (from expect_replies or callbacks)
    responses: list[Activity] = Field(default_factory=list)

    @property
    def is_reply(self) -> bool:
        return self.request_activity is not None
    
    @staticmethod
    def is_allowed_exception(exception: Exception) -> bool:
        return isinstance(exception, (aiohttp.ClientTimeout, aiohttp.ClientConnectionError))
    
    @staticmethod
    async def from_request(
        request_activity: Activity,
        response_or_exception
    ) -> Exchange:
        
        if isinstance(response_or_exception, Exception):
            if not Exchange.is_allowed_exception(response_or_exception):
                raise response_or_exception
            
            return Exchange(
                request_activity=request_activity,
                exception=response_or_exception,
            )
        
        if isinstance(response_or_exception, aiohttp.ClientResponse):
            
            response = cast(aiohttp.ClientResponse, response_or_exception)

            content = await response.json()


            activities = []
            invoke_response = None

            if request_activity.delivery_mode == DeliveryModes.expect_replies:
                body = json.loads(content)
                activities = [ Activity.model_validate(activity) for activity in body ]
                
            elif request_activity.type == ActivityTypes.invoke:
                body = await response.json()
                invoke_response = InvokeResponse.model_validate(status=response.status, body=body)
            else:
                content = await response.text()

            return Exchange(
                request_activity=request_activity,
                response_status=response.status,
                response_content=content,
                received=activities,
                invoke_response=invoke_response
            )
            
        else:
            raise ValueError("response_or_exception must be an Exception or aiohttp.ClientResponse")``