from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    RoleTypes,
)

from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

def AGENTIC_ACTIVITY():
    return Activity(
        type="message",
        recipient=ChannelAccount(
            id="bot_id",
            agentic_app_id=DEFAULTS.agentic_instance_id,
            role=RoleTypes.agentic_instance,
        ),
    )