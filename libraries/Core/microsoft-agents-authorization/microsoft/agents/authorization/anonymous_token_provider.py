from .access_token_provider_base import AccessTokenProviderBase


class AnonymousTokenProvider(AccessTokenProviderBase):
    """
    A class that provides an anonymous token for authentication.
    This is used when no authentication is required.
    """

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return ""
