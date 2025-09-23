from __future__ import annotations

import logging
import jwt
from typing import Optional

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

    async def get_agentic_instance_token(
        self, agent_app_instance_id: str
    ) -> tuple[str, str]:

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
        assert agent_token_result

        # future scenario where we don't know the blueprint id upfront
        token = agent_instance_token["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        agentic_blueprint_id = payload.get("xms_par_app_azp")
        logger.debug("Agentic blueprint id: %s", agentic_blueprint_id)

        # "xms_par_app_azp": "84df77a3-1e3f-4372-a49f-c7e93c3db681",

        return agent_instance_token["access_token"], agent_token_result

    async def get_agentic_user_token(
        self, agent_app_instance_id: str, upn: str, scopes: list[str]
    ) -> Optional[str]:

        if not agent_app_instance_id or not upn:
            raise ValueError(
                "Agent application instance Id and user principal name must be provided."
            )

        instance_token, agent_token = await self.get_agentic_instance_token(
            agent_app_instance_id
        )

        authority = (
            f"https://login.microsoftonline.com/{self._msal_configuration.TENANT_ID}"
        )

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token},
        )

        auth_result_payload = instance_app.acquire_token_for_client(
            scopes,
            data={
                "username": upn,
                "user_federated_identity_credential": instance_token,
                "grant_type": "user_fic",
            },
        )

        return auth_result_payload.get("access_token") if auth_result_payload else None
