import logging

from typing import Optional, Union, TypeVar

from microsoft_agents.activity import (
    Activity,
    TokenResponse
)

from ...turn_context import TurnContext

from .authorization_variant import AuthorizationVariant

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)

class AgenticAuthorization(AuthorizationVariant[StateT]):

    def is_agentic_request(self, context_or_activity: Union[TurnContext, Activity]) -> bool:
        if isinstance(context_or_activity, TurnContext):
            activity = context_or_activity.activity
        else:
            activity = context_or_activity

        return activity.is_agentic()
    
    async def get_agent_instance_id(self, context: TurnContext) -> Optional[str]:
        if not self.is_agentic_request(context):
            return None
        
        return context.activity.recipient.agentic_app_id
    
    def get_agentic_user(self, context: TurnContext) -> Optional[str]:
        if not self.is_agentic_request(context):
            return None
        
        return context.activity.recipient.id
    
    async def get_agentic_instance_token(self, context: TurnContext) -> Optional[str]:

        if not self.is_agentic_request(context):
            return None
        
        connection = self._connection_manager.get_token_provider(context.identity, "agentic")
        return await connection.get_agentic_instance_token(self.get_agent_instance_id(context))

    async def get_agentic_user_token(self, context: TurnContext, scopes: list[str]) -> Optional[str]:
        
        if not self.is_agentic_request(context) or not self.get_agentic_user(context):
            return None
        
        connection = self._connection_manager.get_token_provider(context.identity, "agentic")
        return await connection.get_agentic_user_token(
            await self.get_agentic_instance_token(context), self.get_agentic_user(context), scopes
        )
    
    async def sign_in_user(self, context: TurnContext, exchange_connection: str, scopes: list[str]) -> TokenResponse:
        return await self.get_refreshed_user_token(context, exchange_connection, scopes)
    
    async def get_refreshed_user_token(self, context: TurnContext, exchange_connection: str, scopes: list[str]) -> TokenResponse:
        # not worrying about this for now...
        # if not self._auth_settings.alternate_blueprint_connection_name:
        #     connection = self._connection_manager.get_connection(self._auth_settings.alternate_blueprint_connection_name)
        # else:
        connection = self._connection_manager.get_token_provider(context.identity, "agentic")

        token = await connection.get_agentic_user_token(
            await self.get_agentic_instance_token(context), self.get_agentic_user(context), scopes
        )

        return TokenResponse(token=token)

    async def sign_out_user(self, context: TurnContext) -> None:
        pass