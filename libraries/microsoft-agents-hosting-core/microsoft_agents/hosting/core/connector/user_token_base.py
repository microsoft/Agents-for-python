# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol

from microsoft_agents.activity import (
    TokenResponse,
    TokenStatus,
    TokenOrSignInResourceResponse,
)


class UserTokenBase(Protocol):
    """Base class for user token operations."""

    @abstractmethod
    async def get_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str = None,
        code: str = None,
    ) -> TokenResponse:
        """
        Get sign-in URL.

        :param state: State parameter for OAuth flow.
        :param code_challenge: Code challenge for PKCE.
        :param emulator_url: Emulator URL if used.
        :param final_redirect: Final redirect URL.
        :return: The sign-in URL.
        """
        raise NotImplementedError()

    @abstractmethod
    async def _get_token_or_sign_in_resource(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        state: str,
        code: str = "",
        final_redirect: str = "",
        fwd_url: str = "",
    ) -> TokenOrSignInResourceResponse:
        """
        Gets a token or a sign-in resource for a user and connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param state: State parameter for OAuth flow.
        :param code: Optional authorization code.
        :param final_redirect: Final redirect URL.
        :param fwd_url: Forward URL.
        :return: A token or sign-in resource response.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str = None,
        body: dict = None,
    ) -> dict[str, TokenResponse]:
        """
        Gets Azure Active Directory tokens for a user and connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param body: An optional dictionary containing resource URLs.
        :return: A dictionary of tokens.
        """
        raise NotImplementedError()

    @abstractmethod
    async def sign_out(
        self, user_id: str, connection_name: str = None, channel_id: str = None
    ) -> None:
        """
        Signs the user out from the specified connection.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_token_status(
        self, user_id: str, channel_id: str = None, include: str = None
    ) -> list[TokenStatus]:
        """
        Gets token status for the user.

        :param user_id: ID of the user.
        :param channel_id: ID of the channel.
        :param include: Optional filter.
        :return: A list of token status objects.
        """
        raise NotImplementedError()

    @abstractmethod
    async def exchange_token(
        self, user_id: str, connection_name: str, channel_id: str, body: dict = None
    ) -> TokenResponse:
        """
        Exchanges a token.

        :param user_id: ID of the user.
        :param connection_name: Name of the connection to use.
        :param channel_id: ID of the channel.
        :param body: An optional token exchange request body.
        :return: A token response.
        """
        raise NotImplementedError()
