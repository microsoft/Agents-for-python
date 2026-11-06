"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import logging
import warnings

from typing import (
    Awaitable,
    Callable,
    cast,
    Optional,
    Mapping,
)
from dataclasses import dataclass

from azure.core.credentials_async import AsyncTokenCredential

from microsoft_agents.activity import (
    Activity,
    Channels,
    ChannelId,
    SignInConstants,
    TokenResponse,
)
from microsoft_agents.activity.config import Configuration
from microsoft_agents.activity.activity_types import ActivityTypes

from microsoft_agents.hosting.core.authorization._helpers import (
    _CallableTokenCredential,
)

from ...turn_context import TurnContext
from ...storage import Storage
from ...authorization import Connections
from ..._oauth import _FlowStateTag
from ..state import TurnState
from .auth_handler import AuthHandlerSettings
from ._sign_in_state import _SignInState
from ._sign_in_response import _SignInResponse
from ._handlers import (
    AgenticUserAuthorization,
    ConnectorUserAuthorization,
    _UserAuthorization,
    _AuthorizationHandler,
)
from .authorization_settings import AuthorizationSettings

logger = logging.getLogger(__name__)

AUTHORIZATION_TYPE_MAP = {
    "userauthorization": _UserAuthorization,
    "agenticuserauthorization": AgenticUserAuthorization,
    "connectoruserauthorization": ConnectorUserAuthorization,
}


@dataclass(frozen=True)
class _AuthInterceptResult:
    """Dataclass representing the result of an authentication intercept."""

    should_skip_turn: bool
    should_replay: bool
    continuation_activity: Activity | None = None


class Authorization:
    """Class responsible for managing authorization flows."""

    _storage: Storage
    _connection_manager: Connections
    _handlers: dict[str, _AuthorizationHandler]

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: dict[str, AuthHandlerSettings] | None = None,
        auto_sign_in: bool = False,
        *,
        settings: Configuration | AuthorizationSettings | None = None,
        use_cache: bool = False,
        **kwargs,
    ):
        """Create authorization flows from explicit or configured settings.

        Prefer settings containing a root Configuration from
        ``load_configuration_from_env``, a scoped authorization section/mapping,
        or a bound AuthorizationSettings instance. Root input reads
        ``agent_application::user_authorization``; scoped input reads
        ``handlers`` and ``auto_sign_in`` directly.

        A nonempty auth_handlers mapping replaces configured handlers. Otherwise
        the handlers from settings are used, with the first handler as the
        default. Omitting all configuration creates an instance with no handlers.

        :param storage: The storage system to use for state management.
        :type storage: :class:`microsoft_agents.hosting.core.storage.Storage`
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: :class:`microsoft_agents.hosting.core.authorization.Connections`
        :param auth_handlers: Optional explicit handler IDs and their settings.
        :type auth_handlers: dict[str, AuthHandlerSettings] | None
        :param auto_sign_in: Enable automatic sign-in. False defers to the value
            in settings; it does not override a configured True.
        :param settings: Root/scoped configuration or bound authorization settings.
            When supplied, deprecated kwargs are ignored rather than merged.
        :param use_cache: Retained for compatibility; currently has no effect.
        :param kwargs: Deprecated unpacked root configuration. Emits a
            DeprecationWarning when nonempty, even if settings takes precedence.
        :raises ValueError: If storage is missing or a selected handler has an
            unsupported authorization type or invalid settings.
        """
        if not storage:
            raise ValueError("Storage is required for Authorization")

        self._storage = storage
        self._connection_manager = connection_manager

        self._sign_in_success_handler: Optional[
            Callable[[TurnContext, TurnState, str | None], Awaitable[None]]
        ] = None
        self._sign_in_failure_handler: Optional[
            Callable[[TurnContext, TurnState, str | None], Awaitable[None]]
        ] = None

        if kwargs:
            warnings.warn(
                "Passing configuration via kwargs is deprecated. "
                "Use the 'settings' parameter instead.",
                DeprecationWarning,
            )
            if settings is not None:
                logger.warning(
                    "Both 'settings' and 'kwargs' are provided. 'kwargs' will be ignored in favor of 'settings'."
                )

        auth_settings: AuthorizationSettings
        if settings is None:
            auth_settings = AuthorizationSettings.from_configuration(
                Configuration(kwargs, _is_root_config=True)
            )
        elif isinstance(settings, Mapping):
            auth_settings = AuthorizationSettings.from_mapping(settings)
        elif isinstance(settings, AuthorizationSettings):
            auth_settings = settings

        self._handlers = {}

        self._handler_settings = auth_handlers or auth_settings.handlers
        self._auto_sign_in = auto_sign_in or auth_settings.auto_sign_in

        # operations default to the first handler if none specified
        if self._handler_settings:
            self._default_handler_id = next(iter(self._handler_settings.items()))[0]
            self._init_handlers()

    def _init_handlers(self) -> None:
        """Initialize authorization variants based on the provided auth handlers.

        This method maps the auth types to their corresponding authorization variants, and
        it initializes an instance of each variant that is referenced.

        :param auth_handlers: A dictionary of auth handler configurations.
        :type auth_handlers: dict[str, :class:`microsoft_agents.hosting.core.app.oauth.auth_handler.AuthHandlerSettings`]
        """
        for name, settings in self._handler_settings.items():
            auth_type = settings.auth_type.lower()
            if auth_type not in AUTHORIZATION_TYPE_MAP:
                raise ValueError(f"Auth type {auth_type} not recognized.")

            self._handlers[name] = AUTHORIZATION_TYPE_MAP[auth_type](
                storage=self._storage,
                connection_manager=self._connection_manager,
                settings=settings,
            )

    @property
    def connection_manager(self) -> Connections:
        """
        The connection manager for the authorization instance.

        The connection manager is responsible for managing the connections to the various authentication providers.

        :return: The connection manager.
        :rtype: :class:`microsoft_agents.hosting.core.authorization.Connections`
        """
        return self._connection_manager

    @staticmethod
    def _sign_in_state_key(context: TurnContext) -> str:
        """Generate a unique storage key for the sign-in state based on the context.

        This is the key used to store and retrieve the sign-in state from storage, and
        can be used to inspect or manipulate the state directly if needed.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :return: A unique (across other values of channel_id and user_id) key for the sign-in state.
        :rtype: str
        """
        return f"auth:_SignInState:{context.activity.channel_id}:{context.activity.from_property.id}"

    async def _load_sign_in_state(self, context: TurnContext) -> _SignInState | None:
        """Load the sign-in state from storage for the given context.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :return: The sign-in state if found, None otherwise.
        :rtype: :class:`microsoft_agents.hosting.core.app.oauth._sign_in_state._SignInState` | None
        """
        key = self._sign_in_state_key(context)
        return (await self._storage.read([key], target_cls=_SignInState)).get(key)

    async def _save_sign_in_state(
        self, context: TurnContext, state: _SignInState
    ) -> None:
        """Save the sign-in state to storage for the given context.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param state: The sign-in state to save.
        :type state: :class:`microsoft_agents.hosting.core.app.oauth._sign_in_state._SignInState`
        """
        key = self._sign_in_state_key(context)
        await self._storage.write({key: state})

    async def _delete_sign_in_state(self, context: TurnContext) -> None:
        """Delete the sign-in state from storage for the given context.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        """
        key = self._sign_in_state_key(context)
        await self._storage.delete([key])

    @staticmethod
    def _cache_key(context: TurnContext, handler_id: str) -> str:
        return f"{Authorization._sign_in_state_key(context)}:{handler_id}:token"

    @staticmethod
    def _get_cached_token(
        context: TurnContext, handler_id: str
    ) -> TokenResponse | None:
        key = Authorization._cache_key(context, handler_id)
        return cast(TokenResponse | None, context.turn_state.get(key))

    @staticmethod
    def _cache_token(
        context: TurnContext, handler_id: str, token_response: TokenResponse
    ) -> None:
        key = Authorization._cache_key(context, handler_id)
        context.turn_state[key] = token_response

    @staticmethod
    def _delete_cached_token(context: TurnContext, handler_id: str) -> None:
        key = Authorization._cache_key(context, handler_id)
        if key in context.turn_state:
            del context.turn_state[key]

    def _resolve_handler(self, handler_id: str) -> _AuthorizationHandler:
        """Resolve the auth handler by its ID.

        :param handler_id: The ID of the auth handler to resolve.
        :type handler_id: str
        :return: The corresponding AuthorizationHandler instance.
        :rtype: :class:`microsoft_agents.hosting.core.app.oauth._handlers._AuthorizationHandler`
        :raises ValueError: If the handler ID is not recognized or not configured.
        """
        if handler_id not in self._handlers:
            raise ValueError(
                f"Auth handler {handler_id} not recognized or not configured."
            )
        return self._handlers[handler_id]

    async def _start_or_continue_sign_in(
        self,
        context: TurnContext,
        state: TurnState,
        auth_handler_id: str | None = None,
    ) -> _SignInResponse:
        """Start or continue the sign-in process for the user with the given auth handler.

        _SignInResponse output is based on the result of the variant used by the handler.
        Storage is updated as needed with _SignInState data for caching purposes.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param state: The turn state for the current turn of conversation.
        :type state: :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`
        :param auth_handler_id: The ID of the auth handler to use for sign-in. If None, the first handler will be used.
        :type auth_handler_id: str
        :return: A _SignInResponse indicating the result of the sign-in attempt.
        :rtype: :class:`microsoft_agents.hosting.core.app.oauth._sign_in_response._SignInResponse`
        """

        auth_handler_id = auth_handler_id or self._default_handler_id

        # check cached sign in state
        sign_in_state = await self._load_sign_in_state(context)
        if not sign_in_state:
            # no existing sign-in state, create a new one
            sign_in_state = _SignInState(active_handler_id=auth_handler_id)

        auth_handler_id = sign_in_state.active_handler_id

        handler = self._resolve_handler(auth_handler_id)

        # attempt sign-in continuation (or beginning)
        sign_in_response = await handler._sign_in(context)

        if sign_in_response.tag == _FlowStateTag.COMPLETE:
            if self._sign_in_success_handler:
                await self._sign_in_success_handler(context, state, auth_handler_id)
            await self._delete_sign_in_state(context)
            Authorization._cache_token(
                context, auth_handler_id, sign_in_response.token_response
            )

        elif sign_in_response.tag == _FlowStateTag.FAILURE:
            if self._sign_in_failure_handler:
                await self._sign_in_failure_handler(context, state, auth_handler_id)
            await self._delete_sign_in_state(context)

        elif sign_in_response.tag in [_FlowStateTag.BEGIN, _FlowStateTag.CONTINUE]:
            # Handling special case for Teams SSO, ConsentRequired
            if not (
                ChannelId.get_channel(context.activity.channel_id)
                == Channels.ms_teams.value
                and sign_in_state.continuation_activity
                and context.activity.type == ActivityTypes.invoke
                and context.activity.name
                == SignInConstants.token_exchange_operation_name
            ):
                # store continuation activity and wait for next turn
                sign_in_state.continuation_activity = context.activity
                await self._save_sign_in_state(context, sign_in_state)

        return sign_in_response

    async def sign_out(
        self, context: TurnContext, auth_handler_id: str | None = None
    ) -> None:
        """Attempts to sign out the user from a specified auth handler or the default handler.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: str | None
        :return: None
        """
        auth_handler_id = auth_handler_id or self._default_handler_id
        handler = self._resolve_handler(auth_handler_id)
        Authorization._delete_cached_token(context, auth_handler_id)
        await self._delete_sign_in_state(context)
        await handler._sign_out(context)

    async def _on_turn_auth_intercept(
        self, context: TurnContext, state: TurnState
    ) -> _AuthInterceptResult:
        """Intercepts the turn to check for active authentication flows.

        Returns an _AuthInterceptResult indicating whether the turn should be skipped, replayed, and if a continuation activity is present.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param state: The turn state for the current turn.
        :type state: :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`
        :return: An _AuthInterceptResult indicating whether the turn should be skipped and if a continuation activity is present.
        :rtype: :class:`microsoft_agents.hosting.core.app.oauth.authorization._AuthInterceptResult`
        """
        sign_in_state = await self._load_sign_in_state(context)

        if sign_in_state or self._auto_sign_in:
            auth_handler_id = sign_in_state.active_handler_id if sign_in_state else None
            if auth_handler_id or self._auto_sign_in:
                sign_in_response = await self._start_or_continue_sign_in(
                    context, state, auth_handler_id
                )
                if sign_in_response.tag == _FlowStateTag.COMPLETE:
                    if not sign_in_state:
                        # flow just completed, no continuation activity
                        return _AuthInterceptResult(
                            should_skip_turn=False,
                            should_replay=False,
                            continuation_activity=None,
                        )
                    assert sign_in_state.continuation_activity is not None
                    continuation_activity = (
                        sign_in_state.continuation_activity.model_copy()
                    )
                    # flow complete, start new turn with continuation activity

                    return _AuthInterceptResult(
                        should_skip_turn=True,
                        should_replay=True,
                        continuation_activity=continuation_activity,
                    )
                # auth flow still in progress, the turn should be skipped
                return _AuthInterceptResult(
                    should_skip_turn=True,
                    should_replay=False,
                    continuation_activity=None,
                )
        # no active auth flow, continue processing
        return _AuthInterceptResult(
            should_skip_turn=False, should_replay=False, continuation_activity=None
        )

    async def get_token(
        self,
        context: TurnContext,
        auth_handler_id: str | None = None,
    ) -> TokenResponse:
        """Gets the token for a specific auth handler or the default handler.

        The token is taken from cache, so this does not initiate nor continue a sign-in flow.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param auth_handler_id: The ID of the auth handler to get the token for.
        :type auth_handler_id: str
        :return: The token response from the OAuth provider.
        :rtype: :class:`microsoft_agents.activity.TokenResponse`
        """
        return await self.exchange_token(context, auth_handler_id=auth_handler_id)

    def get_token_as_token_credential(
        self,
        context: TurnContext,
        auth_handler_id: str | None = None,
    ) -> AsyncTokenCredential:
        """Gets the token as an AsyncTokenCredential for a specific auth handler or the default handler.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param auth_handler_id: The ID of the auth handler to get the token for.
        :type auth_handler_id: str | None
        :return: An AsyncTokenCredential for the specified auth handler or the default handler.
        :rtype: :class:`azure.core.credentials_async.AsyncTokenCredential`
        """

        async def func(*scopes: str, **_kwargs) -> TokenResponse:
            return await self.exchange_token(
                context, auth_handler_id=auth_handler_id, scopes=list(scopes)
            )

        return _CallableTokenCredential(func)

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str] | None = None,
        auth_handler_id: str | None = None,
        exchange_connection: str | None = None,
    ) -> TokenResponse:
        """Exchanges or refreshes the token for a specific auth handler or the default handler.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param scopes: The scopes to request during the token exchange or refresh. Defaults
            to the list given in the AuthHandler configuration if None.
        :type scopes: list[str] | None
        :param auth_handler_id: The ID of the auth handler to exchange or refresh the token for.
            If None, the default handler will be used.
        :type auth_handler_id: str | None
        :param exchange_connection: The name of the connection to use for token exchange. If None,
            the connection defined in the AuthHandler configuration will be used.
        :type exchange_connection: str | None
        :return: The token response from the OAuth provider.
        :rtype: :class:`microsoft_agents.activity.TokenResponse`
        :raises ValueError: If the specified auth handler ID is not recognized or not configured.
        """

        auth_handler_id = auth_handler_id or self._default_handler_id
        if auth_handler_id not in self._handlers:
            raise ValueError(
                f"Auth handler {auth_handler_id} not recognized or not configured."
            )

        cached_token = Authorization._get_cached_token(context, auth_handler_id)

        if cached_token:

            handler = self._resolve_handler(auth_handler_id)

            # TODO: for later -> parity with .NET
            # token_res = sign_in_state.tokens[auth_handler_id]
            # if not context.activity.is_agentic_request():
            #     if token_res and not token_res.is_exchangeable():
            #         token = token_res.token
            #         if token.expiration is not None:
            #             diff = token.expiration - datetime.now().timestamp()
            #             if diff > 0:
            #                 return token_res.token

            res = await handler.get_refreshed_token(
                context, exchange_connection, scopes
            )
            if res:
                return res
        return TokenResponse()

    def exchange_token_as_token_credential(
        self,
        context: TurnContext,
        scopes: list[str] | None = None,
        auth_handler_id: str | None = None,
        exchange_connection: str | None = None,
    ) -> AsyncTokenCredential:
        """Gets a token credential that exchanges or refreshes the token for a specific auth handler or the default handler.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param scopes: The scopes to request during the token exchange or refresh. Defaults
            to the list given in the AuthHandler configuration if None.
        :type scopes: list[str] | None
        :param auth_handler_id: The ID of the auth handler to exchange or refresh the token for.
            If None, the default handler will be used.
        :type auth_handler_id: str | None
        :param exchange_connection: The name of the connection to use for token exchange. If None,
            the connection defined in the AuthHandler configuration will be used.
        :type exchange_connection: str | None
        :return: An instance of `AsyncTokenCredential`.
        :rtype: :class:`azure.core.credentials_async.AsyncTokenCredential`
        :raises ValueError: If the specified auth handler ID is not recognized or not configured.
        """
        scopes = list(scopes) if scopes is not None else []

        async def func(*new_scopes: str, **_kwargs) -> TokenResponse:
            all_scopes = list(dict.fromkeys([*scopes, *new_scopes]))
            return await self.exchange_token(
                context,
                scopes=all_scopes,
                auth_handler_id=auth_handler_id,
                exchange_connection=exchange_connection,
            )

        return _CallableTokenCredential(func)

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, str | None], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        :param handler: The handler function to call on successful sign-in.
        :type handler: Callable[[:class:`microsoft_agents.hosting.core.turn_context.TurnContext`, :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`, str | None], Awaitable[None]]
        """
        self._sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, str | None], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.

        :param handler: The handler function to call on sign-in failure.
        :type handler: Callable[[:class:`microsoft_agents.hosting.core.turn_context.TurnContext`, :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`, str | None], Awaitable[None]]
        """
        self._sign_in_failure_handler = handler
