from __future__ import annotations

import json
from typing import cast

from pydantic import BaseModel, Field
import aiohttp

from microsoft_agents.hosting.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

class SRNode(BaseModel):

    # from outgoing activities
    request_activity: Activity | None = None
    response_status: int | None = None
    response_content: str | None = None
    invoke_response: InvokeResponse | None = None
    exception: Exception | None = None


    # from incoming activities, through replies or post post
    received: list[Activity] = Field(default_factory=list)

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
    ) -> SRNode:
        
        if isinstance(response_or_exception, Exception):
            if not SRNode.is_allowed_exception(response_or_exception):
                raise response_or_exception
            
            return SRNode(
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

            return SRNode(
                request_activity=request_activity,
                response_status=response.status,
                response_content=content,
                received=activities,
                invoke_response=invoke_response
            )
            
        else:
            raise ValueError("response_or_exception must be an Exception or aiohttp.ClientResponse")