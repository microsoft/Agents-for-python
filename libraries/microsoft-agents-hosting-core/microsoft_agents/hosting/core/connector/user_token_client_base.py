# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from microsoft_agents.activity import (
    Activity,
    SignInResource,
    TokenExchangeRequest,
    TokenOrSignInResourceResponse,
    TokenResponse,
    TokenStatus,
)

from .agent_sign_in_base import AgentSignInBase
from .user_token_base import UserTokenBase


@runtime_checkable
class UserTokenClientBase(Protocol):
    """UserTokenClientBase is a protocol that defines the interface for a User Token Client."""

    @property
    def agent_sign_in(self) -> AgentSignInBase:
        raise NotImplementedError(
            "agent_sign_in property must be implemented by subclasses."
        )

    @property
    @abstractmethod
    def user_token(self) -> UserTokenBase:
        raise NotImplementedError(
            "user_token property must be implemented by subclasses."
        )

    @abstractmethod
    async def get_user_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        magic_code: str | None = None,
    ) -> TokenResponse:
        raise NotImplementedError(
            "get_user_token method must be implemented by subclasses."
        )

    @abstractmethod
    async def get_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        final_redirect: str | None = None,
    ) -> SignInResource:
        raise NotImplementedError(
            "get_sign_in_resource method must be implemented by subclasses."
        )

    @abstractmethod
    async def sign_out_user(
        self, user_id: str, connection_name: str, channel_id: str
    ) -> None:
        raise NotImplementedError(
            "sign_out_user method must be implemented by subclasses."
        )

    @abstractmethod
    async def get_token_status(
        self,
        user_id: str,
        channel_id: str,
        include: str | None = None,
    ) -> list[TokenStatus]:
        raise NotImplementedError(
            "get_token_status method must be implemented by subclasses."
        )

    @abstractmethod
    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        resource_urls: list[str],
        channel_id: str,
    ) -> dict[str, TokenResponse]:
        raise NotImplementedError(
            "get_aad_tokens method must be implemented by subclasses."
        )

    @abstractmethod
    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        exchange_request: TokenExchangeRequest,
    ) -> TokenResponse:
        raise NotImplementedError(
            "exchange_token method must be implemented by subclasses."
        )

    @abstractmethod
    async def get_token_or_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        code: str | None = None,
        final_redirect: str | None = None,
        fwd_url: str | None = None,
    ) -> TokenOrSignInResourceResponse:
        raise NotImplementedError(
            "get_token_or_sign_in_resource method must be implemented by subclasses."
        )

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release any resources."""
        raise NotImplementedError("close method must be implemented by subclasses.")
