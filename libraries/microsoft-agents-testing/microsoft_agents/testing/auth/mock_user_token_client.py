# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from uuid import uuid4

from microsoft_agents.activity import (
    Activity,
    SignInResource,
    TokenExchangeRequest,
    TokenExchangeResource,
    TokenOrSignInResourceResponse,
    TokenPostResource,
    TokenResponse,
    TokenStatus,
)
from microsoft_agents.hosting.core import UserTokenClientBase

from ._types import (
    UserTokenKey,
    ExchangeableTokenKey,
    TokenMagicCode,
)

_RAISE_EXCEPTION = "_raise_exception"


class MockUserTokenClient(UserTokenClientBase):
    """In-memory stand-in for ``UserTokenClientBase`` used by ``TestAdapter``.

    The mock stores user tokens, magic-code tokens, and token-exchange results
    in dictionaries keyed by connection, channel, and user. It lets tests drive
    OAuth prompt and token-exchange flows without calling the Agents token
    service. Sign-in resources are synthetic and deterministic enough for unit
    tests, but they are not valid service URLs and no network call is made.
    """

    _user_tokens: dict[UserTokenKey, str]
    _exchangable_tokens: dict[ExchangeableTokenKey, str]
    _magic_codes: list[TokenMagicCode]

    def __init__(self):
        """Create an empty in-memory token store."""
        self._user_tokens = {}
        self._exchangable_tokens = {}
        self._magic_codes = []

    @property
    def agent_sign_in(self):
        """Agent sign-in operations are not modeled by this mock client."""
        raise NotImplementedError()

    @property
    def user_token(self):
        """Nested user-token operations are not exposed by this mock client."""
        raise NotImplementedError()

    def add_user_token(
        self,
        *,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str | None = None,
    ) -> None:
        """Add a fake user token that can later be retrieved by OAuth code.

        Without a magic code, the token is returned immediately for the matching
        connection, channel, and user. With a magic code, the token is held in a
        separate one-time list and is promoted to the normal token store only
        when :meth:`get_user_token` is called with the same code.

        :param connection_name: The name of the connection.
        :param channel_id: The channel ID.
        :param user_id: The user ID.
        :param token: The token to be added.
        :param magic_code: An optional magic code associated with the token.
        """
        key = UserTokenKey(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        )

        if magic_code is None:
            self._user_tokens[key] = token
        else:
            self._magic_codes.append(
                TokenMagicCode(key=key, magic_code=magic_code, user_token=token)
            )

    def add_exchangeable_token(
        self,
        *,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ) -> None:
        """Add a fake token-exchange result.

        ``exchangeable_item`` represents either the exchange request token or
        URI. A later :meth:`exchange_token` call for the same connection,
        channel, user, and item returns ``token``.
        """

        key = ExchangeableTokenKey(
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
            exchangeable_item=exchangeable_item,
        )

        self._exchangable_tokens[key] = token

    def raise_on_exchange_request(
        self,
        *,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ) -> None:
        """Make a matching token-exchange request raise an exception.

        This is a test-only way to simulate token service exchange failures
        without a real service.

        :param connection_name: The name of the connection.
        :param channel_id: The channel ID.
        :param user_id: The user ID.
        :param exchangeable_item: The item to be exchanged.
        """
        key = ExchangeableTokenKey(
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
            exchangeable_item=exchangeable_item,
        )

        self._exchangable_tokens[key] = _RAISE_EXCEPTION

    async def get_user_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        magic_code: str | None = None,
    ) -> TokenResponse:
        """Retrieve a fake user token from the in-memory store.

        When ``magic_code`` matches a stored one-time code, the associated token
        is moved into the normal token store before lookup. If no token is found,
        an empty :class:`TokenResponse` is returned.

        :param user_id: The user ID.
        :param connection_name: The name of the connection.
        :param channel_id: The channel ID.
        :param magic_code: An optional magic code associated with the token.
        :return: A TokenResponse containing the token if found, otherwise an empty TokenResponse.
        """

        key = UserTokenKey(
            connection_name=connection_name, user_id=user_id, channel_id=channel_id
        )

        if magic_code is not None:
            index = next(
                (
                    i
                    for i, mc in enumerate(self._magic_codes)
                    if mc.key == key and mc.magic_code == magic_code
                ),
                None,
            )
            if index is not None:
                mc = self._magic_codes.pop(index)
                self.add_user_token(
                    connection_name=connection_name,
                    channel_id=key.channel_id,
                    user_id=key.user_id,
                    token=mc.user_token,
                )

        if key in self._user_tokens:
            token = self._user_tokens[key]
            return TokenResponse(
                token=token,
                connection_name=connection_name,
            )
        return TokenResponse()

    async def get_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        final_redirect: str | None = None,
    ) -> SignInResource:
        """Return a synthetic sign-in resource for tests.

        The returned link and token-exchange resource are fake values derived
        from the connection and activity. They are intended only to let tests
        assert that a sign-in prompt would be sent.

        :param connection_name: The name of the connection.
        :param activity: The activity associated with the sign-in request.
        :param final_redirect: An optional final redirect URL.
        :return: A SignInResource containing the sign-in URL and other details.
        """
        activity_channel_id = activity.channel_id if activity.channel_id else "unknown"
        activity_recipient_id = (
            activity.recipient.id if activity.recipient else "unknown"
        )
        return SignInResource(
            sign_in_link=f"https://fake.com/oauthsignin/{connection_name}/{activity_channel_id}/{activity_recipient_id}",
            token_exchange_resource=TokenExchangeResource(
                id=uuid4().hex, uri=f"api://{connection_name}/resource"
            ),
            token_post_resource=TokenPostResource(
                sas_url=f"https://fake.com/oauthsignin/{connection_name}/token"
            ),
        )

    async def get_token_or_sign_in_resource(
        self,
        connection_name: str,
        activity: Activity,
        code: str | None = None,
        final_redirect: str | None = None,
        fwd_url: str | None = None,
    ) -> TokenOrSignInResourceResponse:
        """Return either a stored token or a synthetic sign-in resource.

        This mirrors the token service shortcut used by OAuth prompts: if a
        token is already available for the activity's user/channel, return it;
        otherwise return a fake sign-in resource.

        :param connection_name: The name of the connection.
        :param activity: The activity associated with the request.
        :param code: An optional magic code associated with the token.
        :param final_redirect: An optional final redirect URL.
        :param fwd_url: An optional forward URL.
        :return: A TokenOrSignInResourceResponse containing either a token or a sign-in resource.
        """

        if not activity.from_property or not activity.from_property.id:
            raise ValueError("Activity must have a valid 'from' property with an 'id'.")

        token_response = await self.get_user_token(
            user_id=activity.from_property.id,
            connection_name=connection_name,
            channel_id=activity.channel_id if activity.channel_id else "unknown",
            magic_code=code,
        )

        if token_response.token:
            return TokenOrSignInResourceResponse(token_response=token_response)

        return TokenOrSignInResourceResponse(
            sign_in_resource=await self.get_sign_in_resource(
                connection_name=connection_name,
                activity=activity,
                final_redirect=final_redirect,
            )
        )

    async def sign_out_user(
        self, user_id: str, connection_name: str, channel_id: str
    ) -> None:
        """Sign out a user by removing matching tokens from the mock store."""
        keys_copy = list(self._user_tokens.keys())
        for key in keys_copy:
            if (
                key.channel_id.casefold() == channel_id.casefold()
                and key.user_id.casefold() == user_id.casefold()
                and key.connection_name.casefold() == connection_name.casefold()
            ):
                self._user_tokens.pop(key)

    async def get_token_status(
        self,
        user_id: str,
        channel_id: str,
        include: str | None = None,
    ) -> list[TokenStatus]:
        """Return token status entries for stored tokens.

        The mock reports a token as present when one exists in the in-memory
        store for the requested user and channel. ``include`` filters by
        connection name.

        :param user_id: The user ID.
        :param channel_id: The channel ID.
        :param include: An optional comma-separated list of connection names to filter the results.
        :return: A list of TokenStatus objects representing the token status for the user.
        """
        include_filter = include.split(",") if include else None
        return [
            TokenStatus(
                connection_name=key.connection_name,
                has_token=True,
                service_provider_display_name=key.connection_name,
            )
            for key in self._user_tokens.keys()
            if key.user_id.casefold() == user_id.casefold()
            and key.channel_id.casefold() == channel_id.casefold()
            and (include_filter is None or key.connection_name in include_filter)
        ]

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        resource_urls: list[str],
        channel_id: str,
    ) -> dict[str, TokenResponse]:
        """Return fake AAD tokens.

        The Python testing mock currently does not model per-resource AAD token
        acquisition, so this returns an empty mapping.
        """
        return {}

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        exchange_request: TokenExchangeRequest,
    ) -> TokenResponse:
        """Exchange a fake token or URI for a stored token response.

        If :meth:`raise_on_exchange_request` configured the matching item to
        fail, this raises an exception. If no matching item is registered, an
        empty :class:`TokenResponse` is returned.

        :param user_id: The user ID.
        :param connection_name: The name of the connection.
        :param channel_id: The channel ID.
        :param exchange_request: The token exchange request containing the token or URI to be exchanged.
        """

        exchangeable_value = exchange_request.token or exchange_request.uri
        if not exchangeable_value:
            raise ValueError(
                "Either token or uri must be provided in the exchange request."
            )

        key = ExchangeableTokenKey(
            connection_name=connection_name,
            user_id=user_id,
            channel_id=channel_id,
            exchangeable_item=exchangeable_value,
        )

        if key in self._exchangable_tokens:
            token = self._exchangable_tokens[key]
            if token == _RAISE_EXCEPTION:
                raise Exception("Simulated exception during token exchange.")

            return TokenResponse(
                channel_id=channel_id, connection_name=connection_name, token=token
            )

        return TokenResponse()

    async def close(self) -> None:
        """Close the mock client.

        The mock owns no network connections or other external resources, so
        this is a no-op.
        """
        # In this mock implementation, there's nothing to close.
        pass
