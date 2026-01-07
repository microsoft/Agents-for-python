"""
Microsoft Graph API client utilities.

This module provides helper functions to interact with Microsoft Graph API
to retrieve user information.
"""

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def get_user_info(access_token: str) -> Optional[dict]:
    """
    Get user information from Microsoft Graph API.

    Args:
        access_token: The Graph API access token

    Returns:
        Dictionary containing user information or None if failed
    """
    graph_api_url = "https://graph.microsoft.com/v1.0/me"

    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
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


async def get_user_display_name(access_token: str) -> str:
    """
    Get the user's display name from Microsoft Graph API.

    Args:
        access_token: The Graph API access token

    Returns:
        The user's display name or "Unknown" if unable to retrieve
    """
    display_name = "Unknown"

    try:
        user_info = await get_user_info(access_token)
        if user_info and "displayName" in user_info:
            display_name = user_info["displayName"]
    except Exception as ex:
        logger.warning(f"Failed to get display name from Graph: {ex}")

    return display_name
