# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    EndOfConversationCodes,
    TurnContextProtocol,
)
from microsoft_agents.hosting.core import ActivityHandler


class EchoAgent(ActivityHandler):
    """A small SDK agent that echoes each A2A message."""

    async def on_message_activity(self, turn_context: TurnContextProtocol):
        text = (turn_context.activity.text or "").strip()

        if text.lower() == "/help":
            response = "Send me a message and I will echo it back."
        elif text:
            response = f"Echo: {text}"
        else:
            response = "I received an empty message."

        await turn_context.send_activity(response)
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.end_of_conversation,
                code=EndOfConversationCodes.completed_successfully,
            )
        )


AGENT = EchoAgent()