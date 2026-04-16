# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any

from microsoft_agents.hosting.core import ConversationState
from microsoft_agents.hosting.core.client import (
    ConversationIdFactoryProtocol,
    ChannelInfoProtocol,
)


@dataclass
class SkillDialogOptions:

    agent_id: str | None = None
    skill_client: Any = None
    skill_host_endpoint: str | None = None
    skill: ChannelInfoProtocol | None = None
    conversation_id_factory: ConversationIdFactoryProtocol | None = None
    conversation_state: ConversationState | None = None
    connection_name: str | None = None
