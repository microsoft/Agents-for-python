import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import aiohttp
from msal import ConfidentialClientApplication

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
)


class BotClient:
    """Python equivalent of the C# BotClient class for sending activities to agents."""
    
    def __init__(
        self,
        messaging_endpoint: str,
        service_endpoint: str,
        cid: str,
        client_id: str,
        tenant_id: str,
        client_secret: str
    ):
        self.messaging_endpoint = messaging_endpoint
        self.service_endpoint = service_endpoint
        self.cid = cid
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        
        # Dictionary to track pending tasks (equivalent to C# ConcurrentDictionary)
        self.task_list: Dict[str, asyncio.Future[List[Activity]]] = {}
        
        # MSAL app for authentication
        self.msal_app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )

    async def send_request(self, activity: Activity) -> str:
        """Send an HTTP request with the activity to the messaging endpoint."""
        
        # Acquire token for authentication
        token_result = self.msal_app.acquire_token_for_client(
            scopes=[f"{self.client_id}/.default"]
        )
        
        if "error" in token_result:
            raise Exception(f"Failed to acquire token: {token_result['error_description']}")
        
        # Update activity properties
        activity.service_url = self.service_endpoint
        if activity.conversation:
            activity.conversation.id = self.cid
        
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {token_result['access_token']}",
            "Content-Type": "application/json"
        }
        
        # Serialize activity to JSON
        activity_json = activity.model_dump(by_alias=True, exclude_none=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.messaging_endpoint,
                headers=headers,
                json=activity_json
            ) as response:
                if not response.ok:
                    raise Exception(f"Failed to send activity: {response.status}")
                
                content = await response.text()
                return content

    async def send_activity(self, activity: Activity) -> List[Activity]:
        """Send an activity and wait for the response."""
        
        # Create a future to track the response
        future: asyncio.Future[List[Activity]] = asyncio.Future()
        self.task_list[self.cid] = future
        
        try:
            # Send activity to the agent
            await self.send_request(activity)
            
            # Wait for response with timeout (20 seconds)
            result = await asyncio.wait_for(future, timeout=20.0)
            return result
        finally:
            # Clean up the task from the list
            self.task_list.pop(self.cid, None)

    async def send_expect_replies_activity(self, activity: Activity) -> List[Activity]:
        """Send an activity with delivery mode expect_replies."""
        
        # Validate that the activity has the correct delivery mode
        if activity.delivery_mode != DeliveryModes.expect_replies:
            raise ValueError("Activity delivery mode must be expect_replies.")
        
        # Send activity to the agent
        content = await self.send_request(activity)
        
        # Parse response
        if not content:
            raise ValueError("No response received from the agent.")
        
        response_data = json.loads(content)
        activities_data = response_data.get("activities", [])
        
        # Convert JSON to Activity objects
        activities = [Activity.model_validate(act_data) for act_data in activities_data]
        return activities

    async def send_stream_activity(self, activity: Activity) -> List[Activity]:
        """Send an activity with delivery mode stream."""
        
        # Validate that the activity has the correct delivery mode
        if activity.delivery_mode != DeliveryModes.stream:
            raise ValueError("Activity delivery mode must be stream.")
        
        # Create a future to track the response
        future: asyncio.Future[List[Activity]] = asyncio.Future()
        self.task_list[self.cid] = future
        
        try:
            # Send activity to the agent
            content = await self.send_request(activity)
            
            # Check if we got an immediate response
            if not content:
                # Wait for streaming response
                result = await asyncio.wait_for(future, timeout=6.0)
                if result:
                    return result
                raise ValueError("No response received from the agent.")
            
            # Parse server-sent events
            lines = [line.strip() for line in content.split("\n\r\n") if line.strip()]
            activities = []
            
            for line in lines:
                if "event: activity" in line:
                    # Extract the data part after "data: "
                    data_parts = line.split("data: ")
                    if len(data_parts) > 1:
                        activity_data = json.loads(data_parts[1])
                        activity = Activity.model_validate(activity_data)
                        activities.append(activity)
                else:
                    raise Exception("Must receive server-sent events")
            
            return activities
        finally:
            # Clean up the task from the list
            self.task_list.pop(self.cid, None)

    async def send_invoke(self, activity: Activity) -> str:
        """Send an invoke activity."""
        
        # Validate that the activity is of type Invoke
        if activity.type != ActivityTypes.invoke:
            raise ValueError("Activity type must be invoke.")
        
        # Send activity to the agent
        content = await self.send_request(activity)
        return content

    def complete_task(self, conversation_id: str, activities: List[Activity]):
        """Complete a pending task with the received activities.
        
        This method should be called by the webhook handler when activities are received.
        """
        future = self.task_list.get(conversation_id)
        if future and not future.done():
            future.set_result(activities)