# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Utility functions for quick agent interactions.

Provides simple functions for sending activities to agents without
needing to set up full scenarios - useful for quick tests and scripts.
"""

from microsoft_agents.activity import Activity
from microsoft_agents.testing.core import (
    Exchange,
    ExternalScenario,
)
from microsoft_agents.testing.core.utils import activities_from_ex

def _create_activity(payload: str | dict | Activity) -> Activity:
    """Create an Activity from various payload types."""
    if isinstance(payload, Activity):
        return payload
    elif isinstance(payload, dict):
        return Activity.model_validate(payload)
    elif isinstance(payload, str):
        return Activity(type="message", text=payload)
    else:
        raise TypeError("Unsupported payload type")

async def ex_send(
    payload: str | dict | Activity,
    url: str,
    listen_duration: float = 1.0,
) -> list[Exchange]:
    """Send an activity to an agent and return the exchanges.
    
    A convenience function for quick agent interactions without setting
    up a full scenario. Creates an ExternalScenario internally.
    
    :param payload: The activity payload (string message, dict, or Activity).
    :param url: The URL of the agent's message endpoint.
    :param listen_duration: Seconds to wait for async responses.
    :return: List of Exchange objects containing responses.
    
    Example::
    
        exchanges = await ex_send("Hello!", "http://localhost:3978/api/messages")
    """
    
    scenario = ExternalScenario(url)

    activity = _create_activity(payload)

    async with scenario.client() as client:
        exchanges = await client.ex_send(activity, wait=listen_duration)
        return exchanges
    
async def send(
    payload: str | dict | Activity,
    url: str,
    listen_duration: float = 1.0,
) -> list[Activity]:
    """Send an activity to an agent and return response activities.
    
    A convenience function that returns just the response Activity objects,
    without the full Exchange metadata.
    
    :param payload: The activity payload (string message, dict, or Activity).
    :param url: The URL of the agent's message endpoint.
    :param listen_duration: Seconds to wait for async responses.
    :return: List of response Activity objects.
    
    Example::
    
        replies = await send("Hello!", "http://localhost:3978/api/messages")
        for reply in replies:
            print(reply.text)
    """
    exchanges = await ex_send(payload, url, listen_duration)
    return activities_from_ex(exchanges)