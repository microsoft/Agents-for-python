from typing import Any

from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential
from microsoft.agents.authorization import AccessTokenProviderBase


class AgentsTokenCredentialAdapter(AsyncTokenCredential):
    def __init__(
        self, token_provider: AccessTokenProviderBase, resource_url: str
    ) -> None:
        self._token_provider = token_provider
        self._resource_url = resource_url

    async def get_token(self, *scopes: tuple[str], **kwargs: Any) -> AccessToken:
        token = await self._token_provider.get_access_token(
            self._resource_url, list(scopes)
        )

        # Return the token with a 1 year expiry
        return AccessToken(token, 31536000)
