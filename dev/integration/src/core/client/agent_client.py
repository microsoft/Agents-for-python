import os
import json
import asyncio
from typing import Any, Optional, cast

from aiohttp import ClientSession

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes
)

from msal import ConfidentialClientApplication

class AgentClient:

    def __init__(
            self,
            messaging_endpoint: str,
            service_endpoint: str,
            cid: str,
            client_id: str,
            tenant_id: str,
            client_secret: str,
            default_timeout: float = 5.0
        ):
        self._messaging_endpoint = messaging_endpoint
        self.service_endpoint = service_endpoint
        self.cid = cid
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        self._headers = None
        self._default_timeout = default_timeout

        self._client = ClientSession(
            base_url=self._messaging_endpoint,
            headers={"Content-Type": "application/json"}
        )

        self._msal_app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )

    async def get_access_token(self) -> str:
        res = self._msal_app.acquire_token_for_client(
            scopes=[f"{self.client_id}/.default"]
        )
        token = res.get("access_token") if res else None
        if not token:
            raise Exception("Could not obtain access token")
        return token
    
    async def _set_headers(self) -> None:
        if not self._headers:
            token = await self.get_access_token()
            self._headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

    async def send_request(self, activity: Activity) -> str:

        await self._set_headers()

        if activity.conversation:
            activity.conversation.id = self.cid

        async with self._client.post(
            self._messaging_endpoint,
            headers=self._headers,
            json=activity.model_dump(by_alias=True, exclude_none=True)
        ) as response:
            if not response.ok:
                raise Exception(f"Failed to send activity: {response.status}")
            content = await response.text()
            return content
        
    def _to_activity(self, activity_or_text: Activity | str) -> Activity:
        if isinstance(activity_or_text, str):
            activity = Activity(
                type=ActivityTypes.message,
                text=activity_or_text,
            )
            return activity
        else:
            return cast(Activity, activity_or_text)

    async def send_activity(self, activity_or_text: Activity | str, timeout: Optional[float] = None) -> str:
        timeout = timeout or self._default_timeout
        activity = self._to_activity(activity_or_text)
        content = await self.send_request(activity)
        return content
    
    async def send_expect_replies(self, activity_or_text: Activity | str, timeout: Optional[float] = None) -> list[Activity]:
        timeout = timeout or self._default_timeout
        activity = self._to_activity(activity_or_text)
        activity.delivery_mode = DeliveryModes.expect_replies

        content = await self.send_request(activity)

        activities_data = json.loads(content).get("activities", [])
        activities = [Activity.model_validate(act) for act in activities_data]
        return activities