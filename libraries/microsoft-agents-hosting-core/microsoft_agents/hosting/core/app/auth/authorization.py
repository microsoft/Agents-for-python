from datetime import datetime
import logging
from typing import TypeVar, Optional, Callable, Awaitable, Generic, cast
import jwt

from microsoft_agents.activity import Activity, TokenResponse

from ...turn_context import TurnContext
from ...storage import Storage
from ...authorization import Connections
from ...oauth import FlowStateTag
from ..state import TurnState
from .auth_handler import AuthHandler
from .sign_in_state import SignInState
from .sign_in_response import SignInResponse
from .handlers import (
    AgenticUserAuthorization,
    UserAuthorization,
    AuthorizationHandler
)

logger = logging.getLogger(__name__)

AUTHORIZATION_TYPE_MAP = {
    UserAuthorization.__name__.lower(): UserAuthorization,
    AgenticUserAuthorization.__name__.lower(): AgenticUserAuthorization,
}

class Authorization:
    """Class responsible for managing authorization flows."""

    _storage: Storage
    _connection_manager: Connections
    _handlers: dict[str, AuthorizationHandler]

    def __init__(
        self,
        storage: Storage,
        connection_manager: Connections,
        auth_handlers: dict[str, AuthHandler] = None,
        auto_signin: bool = None,
        use_cache: bool = False,
        **kwargs,
    ):
        """
        Creates a new instance of Authorization.

        Handlers defined in the configuration (passed in via kwargs) will be used
        only if auth_handlers is empty or None.

        :param storage: The storage system to use for state management.
        :type storage: Storage
        :param connection_manager: The connection manager for OAuth providers.
        :type connection_manager: Connections
        :param auth_handlers: Configuration for OAuth providers.
        :type auth_handlers: dict[str, AuthHandler], optional
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

        if auth_handlers and len(auth_handlers) > 0:
            self._init_auth_variants(auth_handlers)
        else:

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

        # compatibility? TODO
        if not auth_handlers or len(auth_handlers) == 0:
            raise ValueError("At least one auth handler configuration is required.")

        # operations default to the first handler if none specified
        self._default_handler_id = next(iter(self._handler_settings.items()))[0]
        self._init_handlers()

    def _init_handlers(self) -> None:
        """Initialize authorization variants based on the provided auth handlers.

        This method maps the auth types to their corresponding authorization variants, and
        it initializes an instance of each variant that is referenced.

        :param auth_handlers: A dictionary of auth handler configurations.
        :type auth_handlers: dict[str, AuthHandler]
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
    def sign_in_state_key(context: TurnContext) -> str:
        """Generate a unique storage key for the sign-in state based on the context.

        This is the key used to store and retrieve the sign-in state from storage, and
        can be used to inspect or manipulate the state directly if needed.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :return: A unique (across other values of channel_id and user_id) key for the sign-in state.
        :rtype: str
        """
        return f"auth:SignInState:{context.activity.channel_id}:{context.activity.from_property.id}"

    async def _load_sign_in_state(self, context: TurnContext) -> Optional[SignInState]:
        """Load the sign-in state from storage for the given context."""
        key = self.sign_in_state_key(context)
        return (await self._storage.read([key], target_cls=SignInState)).get(key)

    async def _save_sign_in_state(
        self, context: TurnContext, state: SignInState
    ) -> None:
        """Save the sign-in state to storage for the given context."""
        key = self.sign_in_state_key(context)
        await self._storage.write({key: state})

    async def _delete_sign_in_state(self, context: TurnContext) -> None:
        """Delete the sign-in state from storage for the given context."""
        key = self.sign_in_state_key(context)
        await self._storage.delete([key])

    def resolve_handler(self, handler_id: str) -> AuthorizationHandler:
        """Resolve the auth handler by its ID.

        :param handler_id: The ID of the auth handler to resolve.
        :type handler_id: str
        :return: The corresponding AuthorizationHandler instance.
        :rtype: AuthorizationHandler
        :raises ValueError: If the handler ID is not recognized or not configured.
        """
        if handler_id not in self._handlers:
            raise ValueError(
                f"Auth handler {handler_id} not recognized or not configured."
            )
        return self._handlers[handler_id]

    async def start_or_continue_sign_in(
        self, context: TurnContext, state: TurnState, auth_handler_id: Optional[str] = None
    ) -> SignInResponse:
        """Start or continue the sign-in process for the user with the given auth handler.

        SignInResponse output is based on the result of the variant used by the handler.
        Storage is updated as needed with SignInState data for caching purposes.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param state: The turn state for the current turn of conversation.
        :type state: TurnState
        :param auth_handler_id: The ID of the auth handler to use for sign-in. If None, the first handler will be used.
        :type auth_handler_id: str
        :return: A SignInResponse indicating the result of the sign-in attempt.
        :rtype: SignInResponse
        """

        auth_handler_id = auth_handler_id or self._default_handler_id

        # check cached sign in state
        sign_in_state = await self._load_sign_in_state(context)
        if not sign_in_state:
            # no existing sign-in state, create a new one
            sign_in_state = SignInState({auth_handler_id: ""})

        if sign_in_state.tokens.get(auth_handler_id):
            # already signed in with this handler, got it from cached SignInState
            return SignInResponse(
                tag=FlowStateTag.COMPLETE,
                token_response=TokenResponse(
                    token=sign_in_state.tokens[auth_handler_id]
                ),
            )

        handler = self.resolve_handler(auth_handler_id)

        # attempt sign-in continuation (or beginning)
        sign_in_response = await handler.sign_in(context, auth_handler_id, handler.scopes)

        if sign_in_response.tag == FlowStateTag.COMPLETE:
            if self._sign_in_success_handler:
                await self._sign_in_success_handler(context, state, auth_handler_id)
            token = sign_in_response.token_response.token
            sign_in_state.tokens[auth_handler_id] = token
            await self._save_sign_in_state(context, sign_in_state)

        elif sign_in_response.tag == FlowStateTag.FAILURE:
            if self._sign_in_failure_handler:
                await self._sign_in_failure_handler(context, state, auth_handler_id)

        elif sign_in_response.tag in [FlowStateTag.BEGIN, FlowStateTag.CONTINUE]:
            # store continuation activity and wait for next turn
            sign_in_state.continuation_activity = context.activity
            await self._save_sign_in_state(context, sign_in_state)

        return sign_in_response

    async def sign_out(
        self, context: TurnContext, state: TurnState, auth_handler_id: Optional[str] = None
    ) -> None:
        """Attempts to sign out the user from the specified auth handler or all handlers if none specified.

        :param context: The turn context for the current turn of conversation.
        :type context: TurnContext
        :param state: The turn state for the current turn of conversation.
        :type state: TurnState
        :param auth_handler_id: The ID of the auth handler to sign out from. If None, sign out from all handlers.
        :type auth_handler_id: Optional[str]
        :return: None
        """
        auth_handler_id = auth_handler_id or self._default_handler_id
        sign_in_state = await self._load_sign_in_state(context)
        if sign_in_state and auth_handler_id in sign_in_state.tokens:
                # sign out from specific handler
                handler = self.resolve_handler(auth_handler_id)
                await handler.sign_out(context)
                del sign_in_state.tokens[auth_handler_id]
                await self._save_sign_in_state(context, sign_in_state)

    async def on_turn_auth_intercept(
        self, context: TurnContext, state: TurnState
    ) -> tuple[bool, Optional[Activity]]:
        """Intercepts the turn to check for active authentication flows.

        Returns true if the rest of the turn should be skipped because auth did not finish.
        Returns false if the turn should continue processing as normal.
        If auth completes and a new turn should be started, returns the continuation activity
        from the cached SignInState.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param state: The turn state for the current turn.
        :type state: TurnState
        :return: A tuple indicating whether the turn should be skipped and the continuation activity if applicable.
        :rtype: tuple[bool, Optional[Activity]]
        """
        sign_in_state = await self._load_sign_in_state(context)

        if sign_in_state:
            auth_handler_id = sign_in_state.active_handler()
            if auth_handler_id:
                sign_in_response = await self.start_or_continue_sign_in(
                    context, state, auth_handler_id
                )
                if sign_in_response.tag == FlowStateTag.COMPLETE:
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
    ) -> str:
        """Gets the token for a specific auth handler.

        The token is taken from cache, so this does not initiate nor continue a sign-in flow.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param auth_handler_id: The ID of the auth handler to get the token for.
        :type auth_handler_id: str
        :return: The token response from the OAuth provider.
        :rtype: TokenResponse
        """
        return self.exchange_token(context, auth_handler_id)

    async def exchange_token(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None,
        exchange_connection: Optional[str] = None,
        scopes: Optional[list[str]] = None
    ) -> Optional[str]:
        
        handler = self.resolve_handler(auth_handler_id)

        sign_in_state = await self._load_sign_in_state(context)
        if not sign_in_state or not sign_in_state.tokens.get(auth_handler_id):
            return None
        
        token_res = sign_in_state.tokens[auth_handler_id]
        if not context.activity.is_agentic():
            if not token_res.is_exchangeable:
                if token.expiration is not None:
                    diff = token.expiration - datetime.now().timestamp()
                    if diff >= SOME_VALUE:
                        return token_res.token
                    
        handler = self.resolve_handler(auth_handler_id)
        res = await handler.get_refreshed_token(context, auth_handler_id, exchange_connection, scopes)
        if res:
            sign_in_state.tokens[auth_handler_id] = res.token
            await self._save_sign_in_state(context, sign_in_state)
            return res.token
        raise Exception("Failed to exchange token")


    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        :param handler: The handler function to call on successful sign-in.
        """
        self._sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.

        :param handler: The handler function to call on sign-in failure.
        """
        self._sign_in_failure_handler = handler