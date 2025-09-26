import logging

from typing import Optional

from microsoft_agents.activity import TokenResponse

from ...turn_context import TurnContext
from ...oauth import FlowStateTag

from .authorization_variant import AuthorizationVariant
from .sign_in_response import SignInResponse

logger = logging.getLogger(__name__)


class AgenticAuthorization(AuthorizationVariant):
    """Class responsible for managing agentic authorization"""

    async def get_agentic_instance_token(self, context: TurnContext) -> Optional[str]:
        """Gets the agentic instance token for the current agent instance.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :return: The agentic instance token, or None if not an agentic request.
        :rtype: Optional[str]
        """

        if not context.activity.is_agentic():
            return None

        assert context.identity
        connection = self._connection_manager.get_token_provider(
            context.identity, "agentic"
        )
        agent_instance_id = self.get_agent_instance_id(context)
        assert agent_instance_id
        instance_token, _ = await connection.get_agentic_instance_token(
            agent_instance_id
        )
        return instance_token

    async def get_agentic_user_token(
        self, context: TurnContext, scopes: list[str]
    ) -> Optional[str]:
        """Gets the agentic user token for the current agent instance and user.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param scopes: The scopes to request for the token.
        :type scopes: list[str]
        :return: The agentic user token, or None if not an agentic request or no user.
        :rtype: Optional[str]
        """

        if not context.activity.is_agentic() or not self.get_agentic_user(context):
            return None

        assert context.identity
        connection = self._connection_manager.get_token_provider(
            context.identity, "agentic"
        )
        upn = self.get_agentic_user(context)
        agentic_instance_id = self.get_agent_instance_id(context)
        assert upn and agentic_instance_id
        return await connection.get_agentic_user_token(agentic_instance_id, upn, scopes)

    async def sign_in(
        self,
        context: TurnContext,
        connection_name: str,
        scopes: Optional[list[str]] = None,
    ) -> SignInResponse:
        """Retrieves the agentic user token if available.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :param connection_name: The name of the connection to use for sign-in.
        :type connection_name: str
        :param scopes: The scopes to request for the token.
        :type scopes: Optional[list[str]]
        :return: A SignInResponse containing the token response and flow state tag.
        :rtype: SignInResponse
        """
        scopes = scopes or []
        token = await self.get_agentic_user_token(context, scopes)
        return (
            SignInResponse(
                token_response=TokenResponse(token=token), tag=FlowStateTag.COMPLETE
            )
            if token
            else SignInResponse()
        )

    async def sign_out(self, context: TurnContext) -> None:
        """Signs out the agentic user by clearing any stored tokens."""
        pass

    @staticmethod
    def get_agent_instance_id(context: TurnContext) -> Optional[str]:
        """Gets the agent instance ID from the context if it's an agentic request."""
        if not context.activity.is_agentic() or not context.activity.recipient:
            return None
        return context.activity.recipient.agentic_app_id

    @staticmethod
    def get_agentic_user(context: TurnContext) -> Optional[str]:
        """Gets the agentic user (UPN) from the context if it's an agentic request."""
        if not context.activity.is_agentic() or not context.activity.recipient:
            return None
        return context.activity.recipient.id
