"""
Copilot Studio Agent Connector Sample

This agent demonstrates handling requests from Microsoft Copilot Studio via
Power Apps Connector and using OBO token exchange to access Microsoft Graph.
"""

import logging
from os import environ, path
from typing import Optional

import aiohttp
from dotenv import load_dotenv

from microsoft_agents.activity import (
    load_configuration_from_env,
    ActivityTypes,
    RoleTypes,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnContext,
    TurnState,
    turn_context,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(path.join(path.dirname(__file__), ".env"))

# Load configuration from environment
agents_sdk_config = load_configuration_from_env(environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

# Create the agent instance
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config.get("AGENTAPPLICATION", {}),
)


@AGENT_APP.activity(ActivityTypes.message)
async def on_connector_message(context: TurnContext, state: TurnState) -> None:
    """
    Handle messages from Microsoft Copilot Studio connector.

    :param context: The turn context for this turn
    :param state: The turn state
    :param cancellation_token: Cancellation token
    """
    if (
        context.activity.recipient
        and context.activity.recipient.role == RoleTypes.connector_user
    ):
        try:
            # Get the user's OAuth token. Since OBO was configured,
            # it has already been exchanged for a Graph API token.
            if not AGENT_APP.auth:
                await context.send_activity(
                    "Authentication not configured",
                )
                return

            access_token = await AGENT_APP.auth.get_token(context)

            if not access_token or not access_token.token:
                await context.send_activity(
                    "Unable to retrieve access token",
                )
                return

            # Get user's display name from Microsoft Graph
            display_name = await _get_display_name(access_token.token)

            # Send personalized greeting
            await context.send_activity(
                f"Hi, {display_name}!",
            )

        except Exception as ex:
            logger.error(f"Error handling connector message: {ex}", exc_info=True)
            await context.send_activity(
                "Sorry, an error occurred while processing your request.",
            )


async def _get_display_name(token: str) -> str:
    """
    Get the user's display name from Microsoft Graph API.

    :param token: The Graph API access token
    :return: The user's display name or "Unknown" if unable to retrieve
    """
    display_name = "Unknown"

    try:
        graph_info = await _get_graph_info(token)
        if graph_info and "displayName" in graph_info:
            display_name = graph_info["displayName"]
    except Exception as ex:
        logger.warning(f"Failed to get display name from Graph: {ex}")

    return display_name


async def _get_graph_info(token: str) -> Optional[dict]:
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


# Create and start the agent
if __name__ == "__main__":
    from aiohttp.web import Request, Response, Application, run_app
    from microsoft_agents.hosting.aiohttp import (
        start_agent_process,
        jwt_authorization_middleware,
    )

    async def entry_point(req: Request) -> Response:
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    APP = Application(middlewares=[jwt_authorization_middleware])
    APP.router.add_post("/api/messages", entry_point)
    APP.router.add_get("/api/messages", lambda _: Response(status=200))
    APP["agent_configuration"] = (
        CONNECTION_MANAGER.get_default_connection_configuration()
    )
    APP["agent_app"] = AGENT_APP
    APP["adapter"] = AGENT_APP.adapter

    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", "3978"))

    logger.info(f"Starting Copilot Studio Connector sample on {host}:{port}")
    run_app(APP, host=host, port=port)
