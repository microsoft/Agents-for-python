import asyncio
import json

from aiohttp import ClientSession
import pydantic

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

class SenderClient:

    def __init__(self, client: ClientSession):
        self._client: ClientSession = client

    async def _send(self, activity: Activity) -> tuple[int, str]:
        """Send an activity and return the response status and content."""
        
        async with self._client.post(
            "api/messages",
            headers=self._headers,
            json=activity.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
            )
        ) as response:
            content = await response.text()
            if not response.ok:
                raise Exception(f"Failed to send activity: {response.status} - {content}")
            return response.status, content

    async def send(self, activity: Activity) -> str:
        """Send an activity and return the response content as a string."""
        
        _, content = await self._send(activity)
        return content
    
    async def send_expect_replies(
        self,
        activity: Activity,
    ) -> list[Activity]:
        """Send an activity and return the list of reply activities."""
        if activity.delivery_mode != DeliveryModes.expect_replies:
            raise ValueError("Activity delivery_mode must be 'expect_replies'")

        _, content = await self._send(activity)

        raw_activities = json.loads(content).get("activities", [])
        activities = [Activity.model_validate(act) for act in raw_activities]
        
        return activities
    
    async def send_invoke(self, activity: Activity) -> InvokeResponse:
        """Send an invoke activity and return the InvokeResponse."""
        if activity.type != ActivityTypes.invoke:
            raise ValueError("Activity type must be 'invoke'")

        status, content = await self._send(activity)

        try:
            response_data = json.loads(content)
            return InvokeResponse(status=status, body=response_data)
        except pydantic.ValidationError:
            raise ValueError("Invalid InvokeResponse format")
        

    async def submit_card_action(self):
        pass

    async def send_with_attachment(self):
        pass