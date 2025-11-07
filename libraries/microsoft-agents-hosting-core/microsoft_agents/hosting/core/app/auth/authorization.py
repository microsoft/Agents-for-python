"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from datetime import datetime
import logging
from typing import TypeVar, Optional, Callable, Awaitable, Generic, cast
import jwt

from microsoft_agents.activity import Activity, TokenResponse

from ...turn_context import TurnContext
from ...storage import Storage
from ...authorization import Connections
from ..._oauth import _FlowStateTag
from ..state import TurnState
from .auth_handler import AuthHandler
from ._sign_in_state import _SignInState
from ._sign_in_response import _SignInResponse
from ._handlers import (
    AgenticUserAuthorization,
    _UserAuthorization,
    _AuthorizationHandler,
)

logger = logging.getLogger(__name__)

AUTHORIZATION_TYPE_MAP = {
    "userauthorization": _UserAuthorization,
    "agenticuserauthorization": AgenticUserAuthorization,
}


class Authorization:
    """Class responsible for managing authorization flows."""

    _storage: Storage
    _connection_manager: Connections
    _handlers: dict[str, _AuthorizationHandler]

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: Optional[dict[str, AuthHandler]] = None,
        auto_signin: bool = False,
        use_cache: bool = False,
        **kwargs,
    ):
        """
        Creates a new instance of Authorization.

        Handlers defined in the configuration (passed in via kwargs) will be used
        only if auth_handlers is empty or None.

        :param storage: The storage system to use for state management.
        :type storage: :class:`microsoft_agents.hosting.core.storage.Storage`
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: :class:`microsoft_agents.hosting.core.authorization.Connections`
        :param auth_handlers: Configuration for OAuth providers.
        :type auth_handlers: dict[str, :class:`microsoft_agents.hosting.core.app.oauth.auth_handler.AuthHandler`], Optional
        :raises ValueError: When storage is None or no auth handlers provided.
        """
        if not storage:
            raise ValueError("Storage is required for Authorization")

        self._storage = storage
        self._connection_manager = connection_manager

        self._sign_in_success_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None
        self._sign_in_failure_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None

        self._handlers = {}

        if not auth_handlers:
            # get from config
            auth_configuration: dict = kwargs.get("AGENTAPPLICATION", {}).get(
                "USERAUTHORIZATION", {}
            )
            handlers_config: dict[str, dict] = auth_configuration.get("HANDLERS")
            if not auth_handlers and handlers_config:
                auth_handlers = {
                    handler_name: AuthHandler(
                        name=handler_name, **config.get("SETTINGS", {})
                    )
                    for handler_name, config in handlers_config.items()
                }

        self._handler_settings = auth_handlers

        # operations default to the first handler if none specified
        if self._handler_settings:
            self._default_handler_id = next(iter(self._handler_settings.items()))[0]
            self._init_handlers()

    def _init_handlers(self) -> None:
        """Initialize authorization variants based on the provided auth handlers.

        This method maps the auth types to their corresponding authorization variants, and
        it initializes an instance of each variant that is referenced.

        :param auth_handlers: A dictionary of auth handler configurations.
        :type auth_handlers: dict[str, :class:`microsoft_agents.hosting.core.app.oauth.auth_handler.AuthHandler`]
        """
        for name, auth_handler in self._handler_settings.items():
            auth_type = auth_handler.auth_type
            if auth_type not in AUTHORIZATION_TYPE_MAP:
                raise ValueError(f"Auth type {auth_type} not recognized.")

            self._handlers[name] = AUTHORIZATION_TYPE_MAP[auth_type](
                storage=self._storage,
                connection_manager=self._connection_manager,
                auth_handler=auth_handler,
            )

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

    async def _load_sign_in_state(self, context: TurnContext) -> Optional[_SignInState]:
        """Load the sign-in state from storage for the given context.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :return: The sign-in state if found, None otherwise.
        :rtype: Optional[:class:`microsoft_agents.hosting.core.app.oauth._sign_in_state._SignInState`]
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
    ) -> Optional[TokenResponse]:
        key = Authorization._cache_key(context, handler_id)
        return cast(Optional[TokenResponse], context.turn_state.get(key))

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
        auth_handler_id: Optional[str] = None,
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
            # store continuation activity and wait for next turn
            sign_in_state.continuation_activity = context.activity
            await self._save_sign_in_state(context, sign_in_state)

        return sign_in_response

    async def sign_out(
        self, context: TurnContext, auth_handler_id: Optional[str] = None
    ) -> None:
        """Attempts to sign out the user from a specified auth handler or the default handler.

        :param context: The turn context for the current turn of conversation.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: Optional[str]
        :return: None
        """
        auth_handler_id = auth_handler_id or self._default_handler_id
        handler = self._resolve_handler(auth_handler_id)
        Authorization._delete_cached_token(context, auth_handler_id)
        await self._delete_sign_in_state(context)
        await handler._sign_out(context)

    async def _on_turn_auth_intercept(
        self, context: TurnContext, state: TurnState
    ) -> tuple[bool, Optional[Activity]]:
        """Intercepts the turn to check for active authentication flows.

        Returns true if the rest of the turn should be skipped because auth did not finish.
        Returns false if the turn should continue processing as normal.
        If auth completes and a new turn should be started, returns the continuation activity
        from the cached _SignInState.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param state: The turn state for the current turn.
        :type state: :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`
        :return: A tuple indicating whether the turn should be skipped and the continuation activity if applicable.
        :rtype: tuple[bool, Optional[:class:`microsoft_agents.activity.Activity`]]
        """
        sign_in_state = await self._load_sign_in_state(context)

        if sign_in_state:
            auth_handler_id = sign_in_state.active_handler_id
            if auth_handler_id:
                sign_in_response = await self._start_or_continue_sign_in(
                    context, state, auth_handler_id
                )
                if sign_in_response.tag == _FlowStateTag.COMPLETE:
                    assert sign_in_state.continuation_activity is not None
                    continuation_activity = (
                        sign_in_state.continuation_activity.model_copy()
                    )
                    # flow complete, start new turn with continuation activity
                    return True, continuation_activity
                # auth flow still in progress, the turn should be skipped
                return True, None
        # no active auth flow, continue processing
        return False, None

    async def get_token(
        self, context: TurnContext, auth_handler_id: Optional[str] = None
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

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: Optional[list[str]] = None,
        auth_handler_id: Optional[str] = None,
        exchange_connection: Optional[str] = None,
    ) -> TokenResponse:
        """Exchanges or refreshes the token for a specific auth handler or the default handler.

        :param context: The context object for the current turn.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param scopes: The scopes to request during the token exchange or refresh. Defaults
            to the list given in the AuthHandler configuration if None.
        :type scopes: Optional[list[str]]
        :param auth_handler_id: The ID of the auth handler to exchange or refresh the token for.
            If None, the default handler will be used.
        :type auth_handler_id: Optional[str]
        :param exchange_connection: The name of the connection to use for token exchange. If None,
            the connection defined in the AuthHandler configuration will be used.
        :type exchange_connection: Optional[str]
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

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        :param handler: The handler function to call on successful sign-in.
        :type handler: Callable[[:class:`microsoft_agents.hosting.core.turn_context.TurnContext`, :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`, Optional[str]], Awaitable[None]]
        """
        self._sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.

        :param handler: The handler function to call on sign-in failure.
        :type handler: Callable[[:class:`microsoft_agents.hosting.core.turn_context.TurnContext`, :class:`microsoft_agents.hosting.core.app.state.turn_state.TurnState`, Optional[str]], Awaitable[None]]
        """
        self._sign_in_failure_handler = handler
