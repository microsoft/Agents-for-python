"""
Copilot Studio Agent Connector Sample

This agent demonstrates handling requests from Microsoft Copilot Studio via
Power Apps Connector and using OBO token exchange to access Microsoft Graph.
"""

import logging
import aiohttp
from typing import Optional

from microsoft_agents.hosting.core import (
    AgentApplication,
    ApplicationOptions,
    TurnState,
    TurnContext,
)
from microsoft_agents.activity import ActivityTypes, RoleTypes

logger = logging.getLogger(__name__)


class MyAgent(AgentApplication):
    """
    Agent that handles connector requests from Microsoft Copilot Studio.

    This agent:
    - Detects messages from Copilot Studio (connector_user role)
    - Retrieves the OBO-exchanged token
    - Calls Microsoft Graph to get user information
    - Responds with a personalized greeting
    """

    def __init__(self, options: ApplicationOptions):
        super().__init__(options)

        # Register handler for connector messages
        # These are messages where the recipient role is connector_user
        async def is_connector_message(turn_context: TurnContext) -> bool:
            return (
                turn_context.activity.type == ActivityTypes.message
                and turn_context.activity.recipient
                and turn_context.activity.recipient.role == RoleTypes.connector_user
            )

        self.on_activity(is_connector_message, self._on_connector_message)

    async def _on_connector_message(
        self, turn_context: TurnContext, turn_state: TurnState, cancellation_token=None
    ):
        """
        Handle messages from Microsoft Copilot Studio connector.

        :param turn_context: The turn context for this turn
        :param turn_state: The turn state
        :param cancellation_token: Cancellation token
        """
        try:
            # Get the user's OAuth token. Since OBO was configured in appsettings,
            # it has already been exchanged for a Graph API token.
            # If you don't know scopes until runtime, use exchange_turn_token_async instead.
            access_token = await self.user_authorization.get_turn_token_async(
                turn_context, cancellation_token=cancellation_token
            )

            if not access_token:
                await turn_context.send_activity_async(
                    "Unable to retrieve access token",
                    cancellation_token=cancellation_token,
                )
                return

            # Get user's display name from Microsoft Graph
            display_name = await self._get_display_name(access_token)

            # Send personalized greeting
            await turn_context.send_activity_async(
                f"Hi, {display_name}!", cancellation_token=cancellation_token
            )

        except Exception as ex:
            logger.error(f"Error handling connector message: {ex}", exc_info=True)
            await turn_context.send_activity_async(
                "Sorry, an error occurred while processing your request.",
                cancellation_token=cancellation_token,
            )

    async def _get_display_name(self, token: str) -> str:
        """
        Get the user's display name from Microsoft Graph API.

        :param token: The Graph API access token
        :return: The user's display name or "Unknown" if unable to retrieve
        """
        display_name = "Unknown"

        try:
            graph_info = await self._get_graph_info(token)
            if graph_info and "displayName" in graph_info:
                display_name = graph_info["displayName"]
        except Exception as ex:
            logger.warning(f"Failed to get display name from Graph: {ex}")

        return display_name

    async def _get_graph_info(self, token: str) -> Optional[dict]:
        """
        Call Microsoft Graph API to get user information.

        :param token: The Graph API access token
        :return: Dictionary containing user information or None if failed
        """
        graph_api_url = "https://graph.microsoft.com/v1.0/me"

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(graph_api_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(
                            f"Graph API returned status {response.status}: {await response.text()}"
                        )
        except Exception as ex:
            logger.error(f"Error calling Graph API: {ex}", exc_info=True)

        return None
