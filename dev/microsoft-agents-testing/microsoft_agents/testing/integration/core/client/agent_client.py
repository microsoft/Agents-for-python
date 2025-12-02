# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import asyncio
from typing import Optional, cast

from aiohttp import ClientSession
from msal import ConfidentialClientApplication
from pydantic import ValidationError

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    ChannelAccount,
    ConversationAccount,
    InvokeResponse,
)
from microsoft_agents.testing.utils import populate_activity

_DEFAULT_ACTIVITY_VALUES = {
    "service_url": "http://localhost",
    "channel_id": "test_channel",
    "from_property": ChannelAccount(id="sender"),
    "recipient": ChannelAccount(id="recipient"),
    "locale": "en-US",
}


class AgentClient:

    def __init__(
        self,
        agent_url: str,
        cid: str,
        client_id: str,
        tenant_id: str,
        client_secret: str,
        service_url: Optional[str] = None,
        default_activity_data: Optional[Activity | dict] = None,
        default_sleep: float = 0.1,
    ):
        self._agent_url = agent_url
        self._cid = cid
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._client_secret = client_secret
        self._service_url = service_url
        self._headers = None

        self._client: Optional[ClientSession] = None

        self._default_activity_data: Activity | dict = (
            default_activity_data or _DEFAULT_ACTIVITY_VALUES
        )
        self._default_sleep = default_sleep

    @property
    def agent_url(self) -> str:
        return self._agent_url

    @property
    def service_url(self) -> Optional[str]:
        return self._service_url

    async def get_access_token(self) -> str:

        msal_app = ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=self._client_secret,
            authority=f"https://login.microsoftonline.com/{self._tenant_id}",
        )

        res = msal_app.acquire_token_for_client(scopes=[f"{self._client_id}/.default"])
        token = res.get("access_token") if res else None
        if not token:
            raise Exception("Could not obtain access token")
        return token

    async def _init_client(self) -> None:
        if not self._client:
            if self._client_secret:
                token = await self.get_access_token()
                self._headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            else:
                self._headers = {"Content-Type": "application/json"}

            self._client = ClientSession(
                base_url=self._agent_url, headers=self._headers
            )

    async def _send(
        self,
        activity: Activity,
        sleep: float | None = None,
    ) -> str:

        if sleep is None:
            sleep = self._default_sleep

        await self._init_client()
        assert self._client

        if self.service_url:
            activity.service_url = self.service_url

        # activity = populate_activity(activity, self._default_activity_data)

        async with self._client.post(
            "api/messages",
            headers=self._headers,
            json=activity.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
            ),
        ) as response:
            content = await response.text()
            if not response.ok:
                raise Exception(f"Failed to send activity: {response.status}")
            await asyncio.sleep(sleep)
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

    async def send_activity(
        self, activity_or_text: Activity | str, sleep: float | None = None
    ) -> str:
        activity = self._to_activity(activity_or_text)
        content = await self._send(activity, sleep=sleep)
        return content
    
    # async def send_stream(
    #     self, activity_or_text: Activity | str, sleep: float | None = None
    # ) -> list[Activity]:
        
    #     activity = self._to_activity(activity_or_text)
    #     if isinstance(activity_or_text, str):
    #         activity.delivery_mode = DeliveryModes.stream

    #     if not activity.delivery_mode == DeliveryModes.stream:
    #         raise ValueError(
    #             "Activity delivery_mode must be 'stream' for send_stream method."
    #         )

    #     content = await self._send(activity, sleep=sleep)

    #     await asyncio.sleep(5)  # Allow time for all activities to be processed

    #     activities_data = json.loads(content).get("activities", [])
    #     activities = [Activity.model_validate(act) for act in activities_data]

    #     return activities

    async def send_expect_replies(
        self, activity_or_text: Activity | str, sleep: float | None = None
    ) -> list[Activity]:

        activity = self._to_activity(activity_or_text)
        if isinstance(activity_or_text, str):
            activity.delivery_mode = DeliveryModes.expect_replies

        if not activity.delivery_mode == DeliveryModes.expect_replies:
            raise ValueError(
                "Activity delivery_mode must be 'expect_replies' for send_expect_replies method."
            )

        content = await self._send(activity, sleep=sleep)

        activities_data = json.loads(content).get("activities", [])
        activities = [Activity.model_validate(act) for act in activities_data]

        return activities

    async def send_invoke_activity(
        self, activity: Activity, sleep: float | None = None
    ) -> InvokeResponse:

        if not activity.type == ActivityTypes.invoke:
            raise ValueError("Activity type must be 'invoke' for send_invoke method.")

        content = await self._send(activity, sleep=sleep)

        try:
            response_data = json.loads(content)
            return InvokeResponse.model_validate(response_data)
        except ValidationError:
            raise ValueError(
                "Error when sending invoke activity: InvokeResponse not returned or invalid format."
            )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
