from urllib.parse import urlparse

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    ConversationAccount,
    ChannelAccount,
)

def get_host_and_port(url: str) -> tuple[str, int]:
    """Extract host and port from a URL."""

    parsed_url = urlparse(url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    return host, port

def _populate_incoming_activity(activity: Activity) -> Activity:

    activity = activity.model_copy()

    if not activity.locale:
        activity.locale = "en-US"

    if not activity.channel_id:
        activity.channel_id = "emulator"

    if not activity.delivery_mode:
        activity.delivery_mode = DeliveryModes.normal

    if not activity.service_url:
        activity.service_url = "http://localhost"

    if not activity.recipient:
        activity.recipient = ChannelAccount(id="agent", name="Agent")

    if not activity.from_property:
        activity.from_property = ChannelAccount(id="user", name="User")

    if not activity.conversation:
        activity.conversation = ConversationAccount(id="conversation1")

    return activity