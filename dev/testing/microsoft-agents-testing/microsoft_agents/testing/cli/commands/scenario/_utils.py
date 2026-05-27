import json

from microsoft_agents.activity import Activity
from microsoft_agents.testing.cli.core import Output
from microsoft_agents.testing.core import ActivityTemplate

def load_activity(message: str | None, json_file, out: Output) -> Activity:
    """Load an activity from a message or JSON file."""

    if not message and not json_file:
        out.error("Either a message argument or --json_file must be provided.")
        raise ValueError("Either a message argument or --json_file must be provided.")

    if message and json_file:
        out.error("Cannot provide both a message argument and --json_file. Please choose one.")
        raise ValueError("Cannot provide both a message argument and --json_file. Please choose one.")

    activity: Activity
    template = ActivityTemplate().with_defaults({
        "type": "message",
        "channel_id": "test",
        "conversation.id": "test-conversation",
        "locale": "en-US",
        "from.id": "user-id",
        "from.name": "User",
        "recipient.id": "agent-id",
        "recipient.name": "Agent",
    })
    if message:
        assert isinstance(message, str)
        activity = template.create({
            "text": message
        })
    else:
        data = json.load(json_file)
        activity = template.create(data)

    return activity