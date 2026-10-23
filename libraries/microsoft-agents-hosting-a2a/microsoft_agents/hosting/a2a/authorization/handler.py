# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import TokenResponse
from microsoft_agents.hosting.core import (
    Connections,
    Storage,
    TurnContext,
    AuthHandler,
)
from microsoft_agents.hosting.core.app.oauth import (
    _SignInResponse,
    _AuthorizationHandler
)
# from microsoft_agents.hosting.core.app.oauth._handlers import _AuthorizationHandler

class A2AUserAuthorization(_AuthorizationHandler):
    """Authorization handler for A2A user authorization."""

    def __init__(
        self,
        storage: Storage,
        connections: Connections,
        auth_handler: AuthHandler,
        *,
        auth_handler_id: str | None = None,
        auth_handler_settings: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            storage, connections, auth_handler,
            auth_handler_id=auth_handler_id,
            auth_handler_settings=auth_handler_settings,
            **kwargs)

        


    async def _sign_in(self, context: TurnContext, scopes: list[str] | None = None) -> _SignInResponse:
        pass

    async def get_refreshed_token(
        self,
        context: TurnContext,
        exchange_connection: str | None = None,
        exchange_scopes: list[str] | None = None,
    ) -> TokenResponse:

        if 

    async def _sign_out(self, context: TurnContext,) -> None:
        pass