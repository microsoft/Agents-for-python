# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""User Token Client for Microsoft Agents."""

import logging
from aiohttp import ClientSession

from microsoft_agents.hosting.core.connector import UserTokenClientBase
from microsoft_agents.activity import (
    Activity,
    TokenOrSignInResourceResponse,
    TokenResponse,
    TokenStatus,
    SignInResource,
    TokenExchangeRequest,
    TokenExchangeState,
)
from ..get_product_info import get_product_info
from ..user_token_base import UserTokenBase
from ..agent_sign_in_base import AgentSignInBase

from .agent_sign_in import AgentSignIn
from .user_token import UserToken

logger = logging.getLogger(__name__)


class UserTokenClient(UserTokenClientBase):
    """
    UserTokenClient is a client for interacting with the Microsoft M365 Agents SDK User Token API.
    """

    def __init__(
        self,
        endpoint: str,
        token: str,
        *,
        app_id: str | None = None,
        session: ClientSession | None = None,
    ):
        """
        Initialize a new instance of UserTokenClient.

        :param endpoint: The endpoint URL for the token service.
        :param token: The authentication token to use.
        :param app_id: The application ID.
        :param session: The aiohttp ClientSession to use for HTTP requests.
        """
        self._app_id = app_id
        if not self._app_id:
            logger.warning(
                "App ID is not provided. Some operations may not work without an App ID."
                " In the future, creation of UserTokenClient without an App ID will be deprecated."
            )

        if not endpoint.endswith("/"):
            endpoint += "/"

        # Configure headers with JSON acceptance
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": get_product_info(),
        }

        # Create session with the base URL
        session = session or ClientSession(
            base_url=endpoint,
            headers=headers,
        )
        logger.debug(
            "Creating UserTokenClient with endpoint: %s and headers: %s",
            endpoint,
            headers,
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

    @staticmethod
    def _create_token_exchange_state(
        app_id: str,
        connection_name: str,
        activity: Activity,
    ) -> str:
        """
        Creates a token exchange state string.

        :param app_id: The application ID.
        :param connection_name: The connection name.
        :param activity: The activity to use for the token exchange state.
        :return: The token exchange state string.
        """
        return TokenExchangeState(
            connection_name=connection_name,
            conversation=activity.get_conversation_reference(force_base_channel=True),
            relates_to=activity.relates_to,
            ms_app_id=app_id,
        ).get_encoded_state()

    async def get_user_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        magic_code: str | None = None,
    ) -> TokenResponse:
        """
        Gets the user token for a user.

        :param user_id: The ID of the user.
        :param connection_name: The name of the connection.
        :param channel_id: The channel ID associated with the user.
        :param magic_code: The magic code for the token exchange, if any.
        :return: The token response.
        """
        return await self._user_token.get_token(
            user_id,
            connection_name,
            channel_id,
            code=magic_code,
        )

    async def get_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        final_redirect: str | None = None,
    ) -> SignInResource:
        """
        Gets the sign-in resource for a user.

        :param connection_name: The name of the connection.
        :param activity: The activity to use for the sign-in resource.
        :param final_redirect: The final redirect URL after sign-in.
        :return: The sign-in resource.
        """
        if not self._app_id:
            raise ValueError(
                "App ID must be provided in the creation of UserTokenClient to get sign-in resource."
            )

        state = UserTokenClient._create_token_exchange_state(
            self._app_id, connection_name, activity
        )
        return await self._agent_sign_in.get_sign_in_resource(
            state, final_redirect=final_redirect
        )

    async def sign_out_user(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
    ) -> None:
        """
        Signs out a user from the specified connection.

        :param user_id: The ID of the user to sign out.
        :param connection_name: The name of the connection to sign out from.
        :param channel_id: The channel ID associated with the user.
        """
        await self._user_token.sign_out(
            user_id,
            connection_name,
            channel_id,
        )

    async def get_token_status(
        self,
        user_id: str,
        channel_id: str,
        include: str | None = None,
    ) -> list[TokenStatus]:
        """
        Gets the token status for a user.

        :param user_id: The ID of the user.
        :param channel_id: The channel ID associated with the user.
        :param include: Optional filter for included token statuses.
        :return: A list of token statuses.
        """
        return await self._user_token.get_token_status(
            user_id,
            channel_id,
            include=include,
        )

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        resource_urls: list[str],
        channel_id: str,
    ) -> dict[str, TokenResponse]:
        """
        Gets the AAD tokens for a user.

        :param user_id: The ID of the user.
        :param connection_name: The name of the connection.
        :param resource_urls: A list of resource URLs to get tokens for.
        :param channel_id: The channel ID associated with the user.
        :return: A dictionary mapping resource URLs to token responses.
        """
        # todo: verify correctness of resource URL input
        return await self._user_token.get_aad_tokens(
            user_id, connection_name, channel_id, {"resourceUrls": resource_urls}
        )

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        exchange_request: TokenExchangeRequest,
    ) -> TokenResponse:
        """
        Exchanges a token for a user.

        :param user_id: The ID of the user.
        :param connection_name: The name of the connection.
        :param channel_id: The channel ID associated with the user.
        :param exchange_request: The token exchange request.
        :return: The token response.
        """
        return await self._user_token.exchange_token(
            user_id,
            connection_name,
            channel_id,
            exchange_request.model_dump(exclude_none=True),
        )

    async def get_token_or_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        code: str | None = None,
        final_redirect: str | None = None,
        fwd_url: str | None = None,
    ) -> TokenOrSignInResourceResponse:
        """
        Gets the token or sign-in resource for a user.

        :param connection_name: The name of the connection.
        :param activity: The activity to use for the token or sign-in resource.
        :param code: The magic code to use for the token exchange.
        :param final_redirect: The final redirect URL after sign-in.
        :param fwd_url: The forward URL to use for the token exchange.
        :return: The token or sign-in resource.
        """
        if not activity.channel_id:
            raise ValueError(
                "Activity must have a channel_id to get token or sign-in resource."
            )
        if not self._app_id:
            raise ValueError(
                "App ID must be provided in the creation of UserTokenClient to get the token or sign-in resource."
            )

        state = UserTokenClient._create_token_exchange_state(
            self._app_id, connection_name, activity
        )
        return await self._user_token._get_token_or_sign_in_resource(
            user_id=activity.from_property.id,
            connection_name=connection_name,
            channel_id=activity.channel_id,
            state=state,
            code=code or "",
            final_redirect=final_redirect or "",
            fwd_url=fwd_url or "",
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.client:
            logger.debug("Closing UserTokenClient session")
            await self.client.close()
