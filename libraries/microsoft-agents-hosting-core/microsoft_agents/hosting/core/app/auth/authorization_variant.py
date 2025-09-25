from abc import ABC
from typing import Optional
import logging

from microsoft_agents.activity import (
    TokenResponse,
)

from ...turn_context import TurnContext
from ...oauth import FlowStateTag
from ...storage import Storage
from ...authorization import Connections
from .auth_handler import AuthHandler
from .sign_in_response import SignInResponse

logger = logging.getLogger(__name__)

class AuthorizationVariant(ABC):

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

        handlers_config: dict[str, dict] = auth_configuration.get("HANDLERS", {})
        if not auth_handlers and handlers_config:
            auth_handlers = {
                handler_name: AuthHandler(
                    name=handler_name, **config.get("SETTINGS", {})
                )
                for handler_name, config in handlers_config.items()
            }

        self._auth_handlers = auth_handlers or {}
    
    async def sign_in(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None
    ) -> SignInResponse:
        raise NotImplementedError()

    async def sign_out(
        self,
        context: TurnContext,
        auth_handler_id: Optional[str] = None,
    ) -> None:
        raise NotImplementedError()