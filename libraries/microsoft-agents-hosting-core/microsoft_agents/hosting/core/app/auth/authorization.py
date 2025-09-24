import logging
from typing import TypeVar, Optional, Callable, Awaitable, Generic

from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
    Connections
)

from ...oauth import (
    FlowState,
    FlowResponse,
)
from ...storage import Storage
from .auth_handler import AuthHandler
from .user_authorization_base import UserAuthorization
from .agentic_authorization import AgenticAuthorization
from .authorization_variant import AuthorizationClient

AUTHORIZATION_TYPE_MAP: dict[str, type[AuthorizationClient]] = {
    "userauthorization": UserAuthorization,
    "agenticauthorization": AgenticAuthorization
}

logger = logging.getLogger(__name__)
StateT = TypeVar("StateT", bound=TurnState)

class Authorization(Generic[StateT]):
    _authorization_clients: dict[str, AuthorizationClient[StateT]]

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

        Args:
            storage: The storage system to use for state management.
            auth_handlers: Configuration for OAuth providers.

        Raises:
            ValueError: If storage is None or no auth handlers are provided.
        """
        if not storage:
            raise ValueError("Storage is required for Authorization")

        self._storage = storage
        self._connection_manager = connection_manager
        self._authorization_clients = {}

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

        self._auth_handlers = auth_handlers or {}
        self._sign_in_success_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None
        self._sign_in_failure_handler: Optional[
            Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]]
        ] = None

        self._init_auth_clients(self._auth_handlers)

    def _init_auth_clients(self, auth_handlers: dict[str, AuthHandler]):
        auth_types = set(handler.auth_type for handler in auth_handlers.values())
        for auth_type in auth_types:
            self._authorization_clients[auth_type] = AUTHORIZATION_TYPE_MAP[auth_type](
                storage=self._storage,
                connection_manager=self._connection_manager,
                auth_handler=self._auth_handlers.get(auth_type)
            )

    @property
    def user_auth(self) -> UserAuthorization:
        return self._resolve_auth_client(UserAuthorization.__name__)
    
    @property
    def agentic_auth(self) -> AgenticAuthorization:
        return self._resolve_auth_client(AgenticAuthorization.__name__)

    def _resolve_auth_client(self, auth_type_name: Optional[str] = None) -> AuthorizationClient:
        if not auth_type_name:
            return self.user_auth
        
        if auth_type_name not in self._authorization_clients:
            raise ValueError(f"Auth type {auth_type_name} not recognized or not configured.")

        return self._authorization_clients[auth_type_name]

    async def sign_in(self, context: TurnContext, state: StateT, auth_handler_id: Optional[str] = None):
        await self._resolve_auth_client(auth_handler_id).sign_in(context, state, auth_handler_id)

    async def on_turn_auth_intercept(self, context: TurnContext, state: StateT, continue_turn_callback: Callable[[TurnContext], Awaitable[None]]) -> bool:
        """Intercepts the turn to check for active authentication flows.
        
        Returns true if the rest of the turn should be skipped because auth did not finish.
        Returns false if the turn should continue processing as normal.
        Calls continue_turn_callback if auth completes and a new turn should be started. <- TODO, seems a bit strange
        """
        logger.debug(
            "Checking for active sign-in flow for context: %s with activity type %s",
            context.activity.id,
            context.activity.type,
        )
        prev_flow_state = await self._get_active_flow_state(context)
        if prev_flow_state:
            logger.debug(
                "Previous flow state: %s",
                {
                    "user_id": prev_flow_state.user_id,
                    "connection": prev_flow_state.connection,
                    "channel_id": prev_flow_state.channel_id,
                    "auth_handler_id": prev_flow_state.auth_handler_id,
                    "tag": prev_flow_state.tag,
                    "expiration": prev_flow_state.expiration,
                },
            )
        # proceed if there is an existing flow to continue
        # new flows should be initiated in _on_activity
        # this can be reorganized later... but it works for now
        if (
            prev_flow_state
            and (
                prev_flow_state.tag == FlowStateTag.NOT_STARTED
                or prev_flow_state.is_active()
            )
            and context.activity.type in [ActivityTypes.message, ActivityTypes.invoke]
        ):

            logger.debug("Sign-in flow is active for context: %s", context.activity.id)

            flow_response: FlowResponse = await self._auth.begin_or_continue_flow(
                context, turn_state, prev_flow_state.auth_handler_id
            )

            await self._handle_flow_response(context, flow_response)

            new_flow_state: FlowState = flow_response.flow_state
            token_response: TokenResponse = flow_response.token_response
            saved_activity: Activity = new_flow_state.continuation_activity.model_copy()

            if token_response:
                new_context = copy(context)
                new_context.activity = saved_activity
                logger.info("Resending continuation activity %s", saved_activity.text)
                await self.on_turn(new_context)
                await turn_state.save(context)
            return True  # early return from _on_turn
        return False  # continue _on_turn

    async def get_token(
        self, context: TurnContext, auth_handler_id: str
    ) -> TokenResponse:
        """
        Gets the token for a specific auth handler.

        Args:
            context: The context object for the current turn.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        return await self.resolve_auth_client(auth_handler_id).get_token(context, auth_handler_id)

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str],
        auth_handler_id: Optional[str] = None,
    ) -> TokenResponse:
        """
        Exchanges a token for another token with different scopes.

        Args:
            context: The context object for the current turn.
            scopes: The scopes to request for the new token.
            auth_handler_id: Optional ID of the auth handler to use, defaults to first handler.

        Returns:
            The token response from the OAuth provider.
        """
        return await self.resolve_auth_client(auth_handler_id).exchange_token(context, scopes, auth_handler_id)

    def on_sign_in_success(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in is successfully completed.

        Args:
            handler: The handler function to call on successful sign-in.
        """
        self._sign_in_success_handler = handler

    def on_sign_in_failure(
        self,
        handler: Callable[[TurnContext, TurnState, Optional[str]], Awaitable[None]],
    ) -> None:
        """
        Sets a handler to be called when sign-in fails.
        Args:
            handler: The handler function to call on sign-in failure.
        """
        self._sign_in_failure_handler = handler