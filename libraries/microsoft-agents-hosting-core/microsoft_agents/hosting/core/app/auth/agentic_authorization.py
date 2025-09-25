import logging

from typing import Optional, Union, TypeVar

from microsoft_agents.activity import (
    Activity,
    TokenResponse
)
from microsoft_agents.hosting.core.app.auth.sign_in_response import SignInResponse

from ...turn_context import TurnContext

from .authorization_variant import AuthorizationVariant
from .sign_in_response import SignInResponse

logger = logging.getLogger(__name__)

class AgenticAuthorization(AuthorizationVariant):

    def is_agentic_request(self, context_or_activity: Union[TurnContext, Activity]) -> bool:
        if isinstance(context_or_activity, TurnContext):
            activity = context_or_activity.activity
        else:
            activity = context_or_activity

        return activity.is_agentic()
    
    def get_agent_instance_id(self, context: TurnContext) -> Optional[str]:
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
        
        assert context.identity
        connection = self._connection_manager.get_token_provider(context.identity, "agentic")
        agent_instance_id = self.get_agent_instance_id(context)
        assert agent_instance_id
        instance_token, _ = await connection.get_agentic_instance_token(agent_instance_id)
        return instance_token

    async def get_agentic_user_token(self, context: TurnContext, scopes: list[str]) -> Optional[str]:
        
        if not self.is_agentic_request(context) or not self.get_agentic_user(context):
            return None
        
        assert context.identity
        connection = self._connection_manager.get_token_provider(context.identity, "agentic")
        upn = self.get_agentic_user(context)
        agentic_instance_id = self.get_agent_instance_id(context)
        assert upn and agentic_instance_id
        return await connection.get_agentic_user_token(
            agentic_instance_id, upn, scopes
        )
    
    async def sign_in(self, context: TurnContext, connection_name: str, scopes: Optional[list[str]] = None) -> SignInResponse:
        scopes = scopes or []
        token = await self.get_agentic_user_token(context, scopes)
        return SignInResponse(token_response=TokenResponse(token=token), tag=FlowStateTag.COMPLETED) if token else SignInResponse()

    async def sign_out(self, context: TurnContext) -> None:
        pass