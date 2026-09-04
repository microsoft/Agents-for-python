# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime
from typing import Protocol

from azure.core.credentials_async import AsyncTokenCredential
from azure.core.credentials import AccessToken

from microsoft_agents.activity import TokenResponse


class _TokenRetrieverProtocol(Protocol):
    async def __call__(
        self, *scopes: str, **kwargs
    ) -> TokenResponse | AccessToken | None: ...


def _access_token_from_token_response(token_response: TokenResponse) -> AccessToken:
    """Convert a `TokenResponse` to an `AccessToken`.

    :param token_response: An instance of `TokenResponse` to convert.
    :return: An instance of `AccessToken`.
    """
    if not token_response:
        raise ValueError("Failed to retrieve token")

    expires_on: int = 0
    if token_response.expiration:
        exp = token_response.expiration
        if exp.endswith("Z"):
            exp = exp[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(exp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
        expires_on = int(dt.timestamp())

    return AccessToken(token=token_response.token, expires_on=expires_on)


class _CallableTokenCredential(AsyncTokenCredential):
    """A wrapper class that implements `AsyncTokenCredential` using a callable to retrieve tokens."""

    def __init__(self, get_token_callable: _TokenRetrieverProtocol):
        """Initialize the `_CallableTokenCredential` with a token retriever callable.

        :param get_token_callable: A callable that retrieves tokens.
        """
        self._get_token_callable = get_token_callable

    async def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        """Get an access token using the provided callable.

        :param scopes: The scopes for which the access token is requested.
        :param kwargs: Additional keyword arguments to pass to the token retriever callable.
        :return: An instance of `AccessToken`.
        """
        res = await self._get_token_callable(*scopes, **kwargs)
        if not res:
            raise ValueError("Failed to retrieve token")
        if isinstance(res, AccessToken):
            return res
        return _access_token_from_token_response(res)
