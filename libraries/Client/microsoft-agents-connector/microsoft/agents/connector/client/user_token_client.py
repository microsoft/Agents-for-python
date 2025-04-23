# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""User Token Client for Microsoft Agents."""

import logging
from typing import Optional
from aiohttp import ClientSession

from microsoft.agents.connector import UserTokenClientBase
from ..user_token_base import UserTokenBase
from ..agent_sign_in_base import AgentSignInBase


logger = logging.getLogger("microsoft.agents.connector.client.user_token_client")


class AgentSignIn(AgentSignInBase):
    """Implementation of agent sign-in operations."""

    def __init__(self, client: ClientSession):
        self.client = client

    async def get_sign_in_url(
        self, 
        state: str,
        code_challenge: Optional[str] = None,
        emulator_url: Optional[str] = None,
        final_redirect: Optional[str] = None
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

        async with self.client.get("api/agentsignin/getSignInUrl", params=params) as response:
            if response.status >= 400:
                logger.error(f"Error getting sign-in URL: {response.status}")
                response.raise_for_status()
            
            return await response.text()

    async def get_sign_in_resource(
        self, 
        state: str,
        code_challenge: Optional[str] = None,
        emulator_url: Optional[str] = None,
        final_redirect: Optional[str] = None
    ) -> dict:
        """
        Get sign-in resource.

        :param state: State parameter for OAuth flow.
        :param code_challenge: Code challenge for PKCE.
        :param emulator_url: Emulator URL if used.
        :param final_redirect: Final redirect URL.
        :return: The sign-in resource.
        """
        params = {"state": state}
        if code_challenge:
            params["codeChallenge"] = code_challenge
        if emulator_url:
            params["emulatorUrl"] = emulator_url
        if final_redirect:
            params["finalRedirect"] = final_redirect

        async with self.client.get("api/agentsignin/getSignInResource", params=params) as response:
            if response.status >= 400:
                logger.error(f"Error getting sign-in resource: {response.status}")
                response.raise_for_status()
            
            data = await response.json()
            return data


class UserToken(UserTokenBase):
    """Implementation of user token operations."""

    def __init__(self, client: ClientSession):
        self.client = client

    async def get_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: Optional[str] = None,
        code: Optional[str] = None,
    ) -> dict:
        """
        Gets a token for a user and connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param code: Optional authorization code.
        :return: A token response.
        """
        params = {
            "userId": user_id,
            "connectionName": connection_name
        }
        
        if channel_id:
            params["channelId"] = channel_id
        if code:
            params["code"] = code

        async with self.client.get("api/usertoken/GetToken", params=params) as response:
            if response.status >= 400 and response.status != 404:
                logger.error(f"Error getting token: {response.status}")
                response.raise_for_status()
            
            data = await response.json()
            return data

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        channel_id: Optional[str] = None,
        body: Optional[dict] = None,
    ) -> dict:
        """
        Gets Azure Active Directory tokens for a user and connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param body: An optional dictionary containing resource URLs.
        :return: A dictionary of tokens.
        """
        params = {
            "userId": user_id,
            "connectionName": connection_name
        }
        
        if channel_id:
            params["channelId"] = channel_id

        async with self.client.post("api/usertoken/GetAadTokens", params=params, json=body) as response:
            if response.status >= 400:
                logger.error(f"Error getting AAD tokens: {response.status}")
                response.raise_for_status()
            
            data = await response.json()
            return data

    async def sign_out(
        self,
        user_id: str,
        connection_name: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> None:
        """
        Signs the user out from the specified connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        """
        params = {"userId": user_id}
        
        if connection_name:
            params["connectionName"] = connection_name
        if channel_id:
            params["channelId"] = channel_id

        async with self.client.delete("api/usertoken/SignOut", params=params) as response:
            if response.status >= 400 and response.status != 204:
                logger.error(f"Error signing out: {response.status}")
                response.raise_for_status()

    async def get_token_status(
        self,
        user_id: str,
        channel_id: Optional[str] = None,
        include: Optional[str] = None,
    ) -> list:
        """
        Gets token status for the user.

        :param user_id: ID of the user.
        :param channel_id: ID of the channel.
        :param include: Optional filter.
        :return: A list of token status objects.
        """
        params = {"userId": user_id}
        
        if channel_id:
            params["channelId"] = channel_id
        if include:
            params["include"] = include

        async with self.client.get("api/usertoken/GetTokenStatus", params=params) as response:
            if response.status >= 400:
                logger.error(f"Error getting token status: {response.status}")
                response.raise_for_status()
            
            data = await response.json()
            return data

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        body: Optional[dict] = None,
    ) -> dict:
        """
        Exchanges a token.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param body: An optional token exchange request body.
        :return: A token response.
        """
        params = {
            "userId": user_id,
            "connectionName": connection_name,
            "channelId": channel_id
        }

        async with self.client.post("api/usertoken/ExchangeToken", params=params, json=body) as response:
            if response.status >= 400 and response.status != 404:
                logger.error(f"Error exchanging token: {response.status}")
                response.raise_for_status()
            
            data = await response.json()
            return data


class UserTokenClient(UserTokenClientBase):
    """
    UserTokenClient is a client for interacting with the Microsoft M365 Agents SDK User Token API.
    """

    def __init__(self, endpoint: str, token: str, *, session: ClientSession = None):
        """
        Initialize a new instance of UserTokenClient.

        :param endpoint: The endpoint URL for the token service.
        :param token: The authentication token to use.
        :param session: The aiohttp ClientSession to use for HTTP requests.
        """
        if not endpoint.endswith("/"):
            endpoint += "/"

        # Configure headers with JSON acceptance
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Create session with the base URL
        session = session or ClientSession(
            base_url=endpoint,
            headers=headers,
        )

        if len(token) > 1:
            session.headers.update({"Authorization": f"Bearer {token}"})

        self.client = session
        self._agent_sign_in = AgentSignIn(self.client)
        self._user_token = UserToken(self.client)

    @property
    def agent_sign_in(self) -> AgentSignInBase:
        """
        Gets the agent sign-in operations.

        :return: The agent sign-in operations.
        """
        return self._agent_sign_in

    @property
    def user_token(self) -> UserTokenBase:
        """
        Gets the user token operations.

        :return: The user token operations.
        """
        return self._user_token

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.client:
            await self.client.close()