# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from aiohttp import ClientSession

from microsoft_agents.activity import SignInResource
from ..telemetry import user_token_client_spans as spans
from ..agent_sign_in_base import AgentSignInBase
from ._base_client import _BaseClient

logger = logging.getLogger(__name__)


class AgentSignIn(AgentSignInBase, _BaseClient):
    """Implementation of agent sign-in operations."""

    def __init__(self, client: ClientSession):
        _BaseClient.__init__(self, client)

    @property
    def client(self) -> ClientSession:
        """Get the underlying aiohttp ClientSession."""
        return self._client

    @client.setter
    def client(self, value: ClientSession):
        """Set the underlying aiohttp ClientSession."""
        self._client = value

    async def get_sign_in_url(
        self,
        state: str,
        code_challenge: str | None = None,
        emulator_url: str | None = None,
        final_redirect: str | None = None,
    ) -> str:
        """
        Get sign-in URL.

        :param state: State parameter for OAuth flow.
        :param code_challenge: Code challenge for PKCE.
        :param emulator_url: Emulator URL if used.
        :param final_redirect: Final redirect URL.
        :return: The sign-in URL.
        """
        params = {"state": state}
        if code_challenge:
            params["codeChallenge"] = code_challenge
        if emulator_url:
            params["emulatorUrl"] = emulator_url
        if final_redirect:
            params["finalRedirect"] = final_redirect

        logger.info(
            "AgentSignIn.get_sign_in_url(): Getting sign-in URL with params: %s",
            params,
        )

        async with self._wrapped_client().get(
            "api/agentsignin/getSignInUrl", params=params
        ) as response:
            if response.status >= 300:
                logger.error("Error getting sign-in URL: %s", response.status)
                response.raise_for_status()

            return await response.text()

    async def get_sign_in_resource(
        self,
        state: str,
        code_challenge: str | None = None,
        emulator_url: str | None = None,
        final_redirect: str | None = None,
    ) -> SignInResource:
        """
        Get sign-in resource.

        :param state: State parameter for OAuth flow.
        :param code_challenge: Code challenge for PKCE.
        :param emulator_url: Emulator URL if used.
        :param final_redirect: Final redirect URL.
        :return: The sign-in resource.
        """
        with spans.GetSignInResource() as span:
            params = {"state": state}
            if code_challenge:
                params["codeChallenge"] = code_challenge
            if emulator_url:
                params["emulatorUrl"] = emulator_url
            if final_redirect:
                params["finalRedirect"] = final_redirect

            logger.info(
                "AgentSignIn.get_sign_in_resource(): Getting sign-in resource with params: %s",
                params,
            )

            async with self._wrapped_client().get(
                "api/botsignin/getSignInResource", params=params
            ) as response:
                span.share(http_method="GET", status_code=response.status)
                if response.status >= 300:
                    logger.error("Error getting sign-in resource: %s", response.status)
                    response.raise_for_status()

                data = await response.json()
                return SignInResource.model_validate(data)
