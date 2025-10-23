from http import client
import os

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

from msal import ConfidentialClientApplication

class BotClient:

    def __init__(self, messaging_endpoint: str, service_endpoint: str, cid: str, client_id: str, tenant_id: str, client_secret: str):
        self.messaging_endpoint = messaging_endpoint
        self.service_endpoint = service_endpoint
        self.cid = cid
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret

    async def send_request(self, activity: Activity):

        client_id = os.environ["CLIENT_ID"]

        msal_app = ConfidentialClientApplication(
            client_id=client_id,
            tenant_id=os.environ["TENANT_ID"],
            client_credential=os.environ["CLIENT_SECRET"],
        )

        token = msal_app.acquire_token_for_client([f"{client_id}/.default"])

        http_client = 

    async def send_activity(self, activity: Activity):
        pass

    async def send_expect_replies_activity(self, activity: Activity):
        pass

    async def send_stream_activity(self, activity: Activity):
        pass

    async def send_invoke(self, activity: Activity):
        if activity.type != ActivityTypes.invoke:
            raise ValueError("Activity type must be 'invoke' for send_invoke method.")
        return await self.send_request(activity)