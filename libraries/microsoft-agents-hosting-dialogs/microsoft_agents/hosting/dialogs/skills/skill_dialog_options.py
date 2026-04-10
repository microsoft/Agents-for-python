# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import ConversationState
from microsoft_agents.hosting.core.client import (
    ConversationIdFactoryProtocol,
    ChannelInfoProtocol,
)


class SkillDialogOptions:
    def __init__(
        self,
        bot_id: str = None,
        skill_client=None,
        skill_host_endpoint: str = None,
        skill: ChannelInfoProtocol = None,
        conversation_id_factory: ConversationIdFactoryProtocol = None,
        conversation_state: ConversationState = None,
        connection_name: str = None,
    ):
        self.bot_id = bot_id
        self.skill_client = skill_client
        self.skill_host_endpoint = skill_host_endpoint
        self.skill = skill
        self.conversation_id_factory = conversation_id_factory
        self.conversation_state = conversation_state
        self.connection_name = connection_name
