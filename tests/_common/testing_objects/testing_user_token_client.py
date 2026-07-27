# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional, Awaitable
from collections import deque

from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    Channels,
    ResourceResponse,
    RoleTypes,
    InvokeResponse,
    SignInResource,
    TokenExchangeRequest,
    TokenOrSignInResourceResponse,
    TokenResponse,
    TokenStatus,
)
from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.connector import UserTokenClient

AgentCallbackHandler = Callable[[TurnContext], Awaitable]


class _TestingUserTokenOperations:
    def __init__(self, client: "TestingUserTokenClient"):
        self._client = client

    async def get_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        code: str | None = None,
    ) -> TokenResponse | None:
        key = self._client._get_key(connection_name, channel_id, user_id)
        entry = self._client._store.get(key)
        if entry:
            token, stored_code = entry
            if stored_code is None or (code is not None and code == stored_code):
                return TokenResponse(
                    connection_name=connection_name,
                    token=token,
                    channel_id=channel_id,
                )
        return None

    async def sign_out(
        self, user_id: str, connection_name: str, channel_id: str
    ) -> None:
        key = self._client._get_key(connection_name, channel_id, user_id)
        self._client._store.pop(key, None)

    async def exchange_token(
        self, user_id: str, connection_name: str, channel_id: str, body: dict | None
    ) -> TokenResponse | None:
        exchangeable_item = (body or {}).get("token") or (body or {}).get("uri")
        key = self._client._get_exchange_key(
            connection_name, channel_id, user_id, exchangeable_item or ""
        )
        if key in self._client._throw_on_exchange:
            raise Exception("Token exchange not allowed for this item.")
        token = self._client._exchange_store.get(key)
        if token:
            return TokenResponse(
                connection_name=connection_name,
                token=token,
                channel_id=channel_id,
            )
        return None

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
        token_response = await self.get_token(user_id, connection_name, channel_id)
        if token_response:
            return TokenOrSignInResourceResponse(token_response=token_response)
        return TokenOrSignInResourceResponse(
            sign_in_resource=SignInResource(
                sign_in_link=f"https://token.botframework.com/oauthcards?state={state or ''}"
            )
        )

    async def get_token_status(
        self, user_id: str, channel_id: str, include: str | None = None
    ) -> list[TokenStatus]:
        return []


class _TestingAgentSignIn:
    async def get_sign_in_resource(
        self, state: str | None = None, final_redirect: str | None = None
    ) -> SignInResource:
        return SignInResource(
            sign_in_link=f"https://token.botframework.com/oauthcards?state={state or ''}"
        )


# patch userTokenclient
class TestingUserTokenClient(UserTokenClient):
    """A mock user token client for testing."""

    def __init__(self):
        self._store = {}
        self._exchange_store = {}
        self._throw_on_exchange = {}
        self._user_token = _TestingUserTokenOperations(self)
        self._agent_sign_in = _TestingAgentSignIn()

    @property
    def user_token(self) -> _TestingUserTokenOperations:
        return self._user_token

    @property
    def agent_sign_in(self) -> _TestingAgentSignIn:
        return self._agent_sign_in

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str = None,
    ):
        """Add a token for a user that can be retrieved during testing."""
        key = self._get_key(connection_name, channel_id, user_id)
        self._store[key] = (token, magic_code)

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ):
        """Add an exchangeable token for a user that can be exchanged during testing."""
        key = self._get_exchange_key(
            connection_name, channel_id, user_id, exchangeable_item
        )
        self._exchange_store[key] = token

    def throw_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ):
        """Add an instruction to throw an exception during exchange requests."""
        key = self._get_exchange_key(
            connection_name, channel_id, user_id, exchangeable_item
        )
        self._throw_on_exchange[key] = True

    def _get_key(self, connection_name: str, channel_id: str, user_id: str) -> str:
        return f"{connection_name}:{channel_id}:{user_id}"

    def _get_exchange_key(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ) -> str:
        return f"{connection_name}:{channel_id}:{user_id}:{exchangeable_item}"

    async def get_user_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        magic_code: str | None = None,
    ) -> TokenResponse:
        return await self.user_token.get_token(
            user_id, connection_name, channel_id, code=magic_code
        )

    async def get_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        final_redirect: str | None = None,
    ) -> SignInResource:
        return await self.agent_sign_in.get_sign_in_resource(
            final_redirect=final_redirect
        )

    async def sign_out_user(
        self, user_id: str, connection_name: str, channel_id: str
    ) -> None:
        return await self.user_token.sign_out(user_id, connection_name, channel_id)

    async def get_token_status(
        self,
        user_id: str,
        channel_id: str,
        include: str | None = None,
    ) -> list[TokenStatus]:
        return await self.user_token.get_token_status(user_id, channel_id, include)

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        resource_urls: list[str],
        channel_id: str,
    ) -> dict[str, TokenResponse]:
        """
        Get fake AAD tokens for resource URLs using the stored user token.

        The testing adapter stores one token per user/connection/channel. For
        AAD-token requests, mirror that token across each requested resource URL.
        """
        key = self._get_key(connection_name, channel_id, user_id)
        entry = self._store.get(key)
        if not entry:
            return {}

        token, _ = entry
        return {
            resource_url: TokenResponse(
                connection_name=connection_name,
                token=token,
                channel_id=channel_id,
            )
            for resource_url in resource_urls
        }

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        exchange_request: TokenExchangeRequest,
    ) -> TokenResponse:
        return await self.user_token.exchange_token(
            user_id,
            connection_name,
            channel_id,
            body=exchange_request.model_dump(exclude_none=True),
        )

    async def get_token_or_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        code: str | None = None,
        final_redirect: str | None = None,
        fwd_url: str | None = None,
    ) -> TokenOrSignInResourceResponse:
        return await self.user_token._get_token_or_sign_in_resource(
            activity.from_property.id,
            connection_name,
            activity.channel_id,
            "",
            code or "",
            final_redirect or "",
            fwd_url or "",
        )
