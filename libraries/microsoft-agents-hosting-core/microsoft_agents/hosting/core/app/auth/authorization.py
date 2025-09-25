import logging
from typing import TypeVar, Optional, Callable, Awaitable, Generic, cast
import jwt

from microsoft_agents.activity import Activity, TokenResponse

from tests.hosting_core.app import auth

from ...turn_context import TurnContext
from ...storage import Storage
from ...authorization import Connections
from ...oauth import FlowStateTag
from ..state import TurnState
from .auth_handler import AuthHandler
from .user_authorization import UserAuthorization
from .agentic_authorization import AgenticAuthorization
from .authorization_variant import AuthorizationVariant
from .sign_in_state import SignInState
from .sign_in_response import SignInResponse

AUTHORIZATION_TYPE_MAP: dict[str, type[AuthorizationVariant]] = {
    UserAuthorization.__name__.lower(): UserAuthorization,
    AgenticAuthorization.__name__.lower(): AgenticAuthorization,
}

logger = logging.getLogger(__name__)
StateT = TypeVar("StateT", bound=TurnState)


class Authorization(Generic[StateT]):
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

        self._authorization_variants = {}
        self._init_auth_variants(self._auth_handlers)

    def _init_auth_variants(self, auth_handlers: dict[str, AuthHandler]):
        auth_types = set(handler.auth_type for handler in auth_handlers.values())
        for auth_type in auth_types:
            auth_type = auth_type.lower()

            associated_handlers = {
                auth_handler.name: auth_handler
                for auth_handler in self._auth_handlers.values()
                if auth_handler.auth_type.lower() == auth_type
            }

            self._authorization_variants[auth_type] = AUTHORIZATION_TYPE_MAP[auth_type](
                storage=self._storage,
                connection_manager=self._connection_manager,
                auth_handlers=associated_handlers,
            )

    def sign_in_state_key(self, context: TurnContext) -> str:
        return f"auth:SignInState:{context.activity.channel_id}:{context.activity.from_property.id}"

    async def _load_sign_in_state(self, context: TurnContext) -> Optional[SignInState]:
        key = self.sign_in_state_key(context)
        return (await self._storage.read([key], target_cls=SignInState)).get(key)

    async def _save_sign_in_state(
        self, context: TurnContext, state: SignInState
    ) -> None:
        key = self.sign_in_state_key(context)
        await self._storage.write({key: state})

    async def _delete_sign_in_state(self, context: TurnContext) -> None:
        key = self.sign_in_state_key(context)
        await self._storage.delete([key])

    @property
    def user_auth(self) -> UserAuthorization:
        return cast(
            UserAuthorization, self._resolve_auth_variant(UserAuthorization.__name__)
        )

    @property
    def agentic_auth(self) -> AgenticAuthorization:
        return cast(
            AgenticAuthorization,
            self._resolve_auth_variant(AgenticAuthorization.__name__),
        )

    def _resolve_auth_variant(self, auth_variant: str) -> AuthorizationVariant:

        auth_variant = auth_variant.lower()
        if auth_variant not in self._authorization_variants:
            raise ValueError(
                f"Auth variant {auth_variant} not recognized or not configured."
            )

        return self._authorization_variants[auth_variant]

    def resolve_handler(self, handler_id: str) -> AuthHandler:
        if handler_id not in self._auth_handlers:
            raise ValueError(
                f"Auth handler {handler_id} not recognized or not configured."
            )
        return self._auth_handlers[handler_id]

    async def start_or_continue_sign_in(
        self, context: TurnContext, state: StateT, auth_handler_id: str
    ) -> SignInResponse:

        sign_in_state = await self._load_sign_in_state(context)
        if not sign_in_state:
            sign_in_state = SignInState({auth_handler_id: ""})

        if sign_in_state.tokens.get(auth_handler_id):
            return SignInResponse(
                tag=FlowStateTag.COMPLETE,
                token_response=TokenResponse(
                    token=sign_in_state.tokens[auth_handler_id]
                ),
            )

        handler = self.resolve_handler(auth_handler_id)
        variant = self._resolve_auth_variant(handler.auth_type)
        sign_in_response = await variant.sign_in(context, auth_handler_id)

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
            sign_in_state.continuation_activity = context.activity
            await self._save_sign_in_state(context, sign_in_state)

        return sign_in_response

    async def sign_out(
        self, context: TurnContext, state: StateT, auth_handler_id=None
    ) -> None:
        sign_in_state = await self._load_sign_in_state(context)
        if sign_in_state:
            if not auth_handler_id:
                for handler_id in sign_in_state.tokens.keys():
                    if handler_id in sign_in_state.tokens:
                        handler = self.resolve_handler(handler_id)
                        variant = self._resolve_auth_variant(handler.auth_type)
                        await variant.sign_out(context, handler_id)
                await self._delete_sign_in_state(context)
            elif auth_handler_id in sign_in_state.tokens:
                handler = self.resolve_handler(auth_handler_id)
                variant = self._resolve_auth_variant(handler.auth_type)
                await variant.sign_out(context, auth_handler_id)
                del sign_in_state.tokens[auth_handler_id]
                await self._save_sign_in_state(context, sign_in_state)

    async def on_turn_auth_intercept(
        self, context: TurnContext, state: StateT
    ) -> tuple[bool, Optional[Activity]]:
        """Intercepts the turn to check for active authentication flows.

        Returns true if the rest of the turn should be skipped because auth did not finish.
        Returns false if the turn should continue processing as normal.
        Calls continue_turn_callback if auth completes and a new turn should be started. <- TODO, seems a bit strange
        """

        # get active thing...

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
                    return True, continuation_activity
                return True, None
        return False, None

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
        sign_in_state = await self._load_sign_in_state(context)
        if not sign_in_state or not sign_in_state.tokens.get(auth_handler_id):
            return TokenResponse()
        token = sign_in_state.tokens[auth_handler_id]
        return TokenResponse(token=token)

    async def exchange_token(
        self,
        context: TurnContext,
        scopes: list[str],
        auth_handler_id: str,
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

        token_response = await self.get_token(context, auth_handler_id)

        if token_response and self._is_exchangeable(token_response.token):
            logger.debug("Token is exchangeable, performing OBO flow")
            return await self._handle_obo(token_response.token, scopes, auth_handler_id)

        return token_response

    def _is_exchangeable(self, token: str) -> bool:
        """
        Checks if a token is exchangeable (has api:// audience).

        Args:
            token: The token to check.

        Returns:
            True if the token is exchangeable, False otherwise.
        """
        try:
            # Decode without verification to check the audience
            payload = jwt.decode(token, options={"verify_signature": False})
            aud = payload.get("aud")
            return isinstance(aud, str) and aud.startswith("api://")
        except Exception:
            logger.error("Failed to decode token to check audience")
            return False

    async def _handle_obo(
        self, token: str, scopes: list[str], handler_id: str = None
    ) -> TokenResponse:
        """
        Handles On-Behalf-Of token exchange.

        Args:
            context: The context object for the current turn.
            token: The original token.
            scopes: The scopes to request.

        Returns:
            The new token response.

        """
        auth_handler = self.resolve_handler(handler_id)
        token_provider = self._connection_manager.get_connection(
            auth_handler.obo_connection_name
        )

        logger.info("Attempting to exchange token on behalf of user")
        new_token = await token_provider.aquire_token_on_behalf_of(
            scopes=scopes,
            user_assertion=token,
        )
        return TokenResponse(token=new_token)

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
