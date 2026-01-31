from microsoft_agents.activity import Activity
from microsoft_agents.testing.core import (
    ActivityTemplate,
    ScenarioConfig,
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
    
    """Send an activity to the specified URL and listen for responses.

    Args:
        payload: The activity payload to send (str, dict, or Activity).
        url: The URL of the agent to send the activity to.
        listen_duration: Duration in seconds to listen for responses.
        """
    
    scenario = ExternalScenario(
        url,
        ScenarioConfig(
            activity_template = ActivityTemplate(),
        )
    )

    activity = _create_activity(payload)

    async with scenario.client() as client:
        exchanges = await client.ex_send(activity, wait=listen_duration)
        return exchanges
    
async def send(
    payload: str | dict | Activity,
    url: str,
    listen_duration: float = 1.0,
) -> list[Activity]:
    exchanges = await ex_send(payload, url, listen_duration)
    return activities_from_ex(exchanges)