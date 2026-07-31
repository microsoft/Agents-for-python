# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from aiohttp import ClientResponseError, ClientSession

from microsoft_agents.activity import (
    ChannelId,
    TokenOrSignInResourceResponse,
    TokenResponse,
    TokenStatus,
)
from ..telemetry import user_token_client_spans as spans
from ..user_token_base import UserTokenBase
from .._utils import _handle_request_error
from ._base_client import _BaseClient

logger = logging.getLogger(__name__)


class UserToken(UserTokenBase, _BaseClient):
    """Implementation of user token operations."""

    def __init__(self, client: ClientSession):
        _BaseClient.__init__(self, client)
        self.client = self._client

    @property
    def client(self) -> ClientSession:
        """Get the underlying aiohttp ClientSession."""
        return self._client

    @client.setter
    def client(self, value: ClientSession):
        """Set the underlying aiohttp ClientSession."""
        self._client = value

    async def get_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str | None = None,
        code: str | None = None,
    ) -> TokenResponse:

        channel_id = ChannelId.get_channel(channel_id)

        with spans.GetUserToken(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        ) as span:
            params = {"userId": user_id, "connectionName": connection_name}

            if channel_id:
                params["channelId"] = channel_id
            if code:
                params["code"] = code

            safe_params = dict(params)
            if "code" in safe_params:
                safe_params["code"] = "<redacted>"

            logger.info(
                "UserToken.get_token(): Getting token with params: %s", safe_params
            )
            async with self._wrapped_client().get(
                "api/usertoken/GetToken", params=params
            ) as response:
                span.share(http_method="GET", status_code=response.status)

                if response.status == 404:
                    logger.warning(
                        "404: Could be issue with magic code or user not found. Returning empty token response."
                    )
                    return TokenResponse()
                elif response.status != 200:
                    _handle_request_error(
                        logger, response, resource="api/usertoken/GetToken"
                    )

                data = await response.json()
                return TokenResponse.model_validate(data)

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
        """Get token or sign-in resource for a user."""

        channel_id = ChannelId.get_channel(channel_id)

        with spans.GetTokenOrSignInResource(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        ) as span:
            params = {
                "userId": user_id,
                "connectionName": connection_name,
                "channelId": channel_id,
                "state": state,
                "code": code,
                "finalRedirect": final_redirect,
                "fwdUrl": fwd_url,
            }

            logger.info("Getting token or sign-in resource with params: %s", params)
            async with self._wrapped_client().get(
                "/api/usertoken/GetTokenOrSignInResource", params=params
            ) as response:
                span.share(http_method="GET", status_code=response.status)

                if response.status != 200:
                    _handle_request_error(
                        logger,
                        response,
                        resource="/api/usertoken/GetTokenOrSignInResource",
                    )

                data = await response.json()
                return TokenOrSignInResourceResponse.model_validate(data)

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str | None = None,
        body: dict | None = None,
    ) -> dict[str, TokenResponse]:
        """Get AAD tokens for a user."""

        channel_id = ChannelId.get_channel(channel_id)

        with spans.GetAadTokens(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        ) as span:
            params = {"userId": user_id, "connectionName": connection_name}

            if channel_id:
                params["channelId"] = channel_id

            logger.info("Getting AAD tokens with params: %s and body: %s", params, body)
            async with self._wrapped_client().post(
                "api/usertoken/GetAadTokens", params=params, json=body
            ) as response:
                span.share(http_method="POST", status_code=response.status)

                if response.status != 200:
                    _handle_request_error(
                        logger, response, resource="api/usertoken/GetAadTokens"
                    )

                data = await response.json()
                return {k: TokenResponse.model_validate(v) for k, v in data.items()}

    async def sign_out(
        self,
        user_id: str,
        connection_name: str | None = None,
        channel_id: str | None = None,
    ) -> None:
        """Sign out user from a connection."""

        channel_id = ChannelId.get_channel(channel_id)

        with spans.SignOut(
            user_id=user_id, connection_name=connection_name, channel_id=channel_id
        ) as span:
            params = {"userId": user_id}

            if connection_name:
                params["connectionName"] = connection_name
            if channel_id:
                params["channelId"] = channel_id

            logger.info("Signing out user %s with params: %s", user_id, params)
            async with self._wrapped_client().delete(
                "api/usertoken/SignOut", params=params
            ) as response:
                span.share(http_method="DELETE", status_code=response.status)

                if response.status not in (200, 204):
                    _handle_request_error(
                        logger, response, resource="api/usertoken/SignOut"
                    )

    async def get_token_status(
        self,
        user_id: str,
        channel_id: str | None = None,
        include: str | None = None,
    ) -> list[TokenStatus]:
        """Get token status for a user."""

        channel_id = ChannelId.get_channel(channel_id)

        with spans.GetTokenStatus(user_id=user_id, channel_id=channel_id) as span:
            params = {"userId": user_id}

            if channel_id:
                params["channelId"] = channel_id
            if include:
                params["include"] = include

            logger.info(
                "Getting token status for user %s with params: %s", user_id, params
            )
            async with self._wrapped_client().get(
                "api/usertoken/GetTokenStatus", params=params
            ) as response:
                span.share(http_method="GET", status_code=response.status)

                if response.status != 200:
                    _handle_request_error(
                        logger, response, resource="api/usertoken/GetTokenStatus"
                    )

                data = await response.json()
                return [TokenStatus.model_validate(status) for status in data]

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        body: dict | None = None,
    ) -> TokenResponse:
        """Exchange token for a user."""

        channel_id = ChannelId.get_channel(channel_id)

        with spans.ExchangeToken(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        ) as span:
            params = {
                "userId": user_id,
                "connectionName": connection_name,
                "channelId": channel_id,
            }

            logger.info(
                "Exchanging token with params: %s (body keys: %s)",
                params,
                list(body.keys()) if isinstance(body, dict) else None,
            )
            async with self._wrapped_client().post(
                "api/usertoken/exchange", params=params, json=body
            ) as response:
                span.share(http_method="POST", status_code=response.status)

                if response.status >= 300:
                    response_text = await response.text("utf-8")
                    logger.error(
                        "Error exchanging token: %s %s",
                        response.status,
                        response_text,
                    )
                    raise ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=response_text,
                        headers=response.headers,
                    )

                data = await response.json()
                return TokenResponse.model_validate(data)
