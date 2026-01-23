# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.testing.utils import ActivityTemplate

DEFAULT_ACTIVITY_TEMPLATE = ActivityTemplate({
    "type": "message",
    "channel_id": "test",
    "conversation.id": "conv-id",
    "locale": "en-US",
    "from.id": "user-id",
    "from.name": "User",
    "recipient.id": "agent-id",
    "recipient.name": "Agent",
    "text": "",
})

class AgentScenarioConfig:

    env_file_path: str = ".env"
    response_server_port: int = 9378

    activity_template: ActivityTemplate = DEFAULT_ACTIVITY_TEMPLATE