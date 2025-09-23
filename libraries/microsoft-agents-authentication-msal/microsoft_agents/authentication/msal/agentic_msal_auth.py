from __future__ import annotations

import logging
from typing import Optional

import aiohttp
from msal import ConfidentialClientApplication

from .msal_auth import MsalAuth

logger = logging.getLogger(__name__)


class AgenticMsalAuth(MsalAuth):

    # the call to MSAL is blocking, but in the future we want to create an asyncio task
    # to avoid this
    async def get_agentic_application_token(
        self, agent_app_instance_id: str
    ) -> Optional[str]:

        if not agent_app_instance_id:
            raise ValueError("Agent application instance Id must be provided.")

        msal_auth_client = self._create_client_application()

        if isinstance(msal_auth_client, ConfidentialClientApplication):

            # https://github.dev/AzureAD/microsoft-authentication-library-for-dotnet
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                ["api://AzureAdTokenExchange/.default"],
                data={"fmi_path": agent_app_instance_id},
            )

            if auth_result_payload:
                return auth_result_payload.get("access_token")

        return None

    async def get_agentic_instance_token(self, agent_app_instance_id: str) -> str:

        if not agent_app_instance_id:
            raise ValueError("Agent application instance Id must be provided.")

        agent_token_result = await self.get_agentic_application_token(
            agent_app_instance_id
        )

        authority = (
            f"https://login.microsoftonline.com/{self._msal_configuration.TENANT_ID}"
        )

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token_result},
        )

        agent_instance_token = instance_app.acquire_token_for_client(
            ["api://AzureAdTokenExchange/.default"]
        )

        assert agent_instance_token
        return agent_instance_token["access_token"]

    # async def get_agentic_user_token(self, agent_app_instance_id: str, upn: str, scopes: list[str]) -> Optional[str]:

    #     if not agent_app_instance_id or not upn:
    #         raise ValueError("Agent application instance Id and user principal name must be provided.")

    #     agent_token = await self.get_agentic_application_token(agent_app_instance_id)
    #     instance_token = await self.get_agentic_instance_token(agent_app_instance_id)

    #     token_endpoint = f"https://login.microsoftonline.com/{self._msal_configuration.TENANT_ID}/oauth2/v2.0/token"

    #     parameters = {
    #         "client_id": agent_app_instance_id,
    #         "scope": " ".join(scopes),
    #         "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    #         "client_assertion": agent_token,
    #         "username": upn,
    #         "user_federated_identity_credential": instance_token,
    #         "grant_type": "user_fic"
    #     }

    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(
    #             token_endpoint,
    #             data=parameters,
    #             headers={"Content-Type": "application/x-www-form-urlencoded"}
    #         ) as response:

    #             if response.status >= 400:
    #                 logger.error("Failed to acquire user federated identity token: %s", response.status)
    #                 response.raise_for_status()

    #             token_response = await response.json()

    #             if token_response:
    #                 return token_response.get("access_token")

    #             return None
