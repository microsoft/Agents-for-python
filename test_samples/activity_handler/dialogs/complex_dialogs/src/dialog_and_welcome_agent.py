# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import (
    ConversationState,
    MessageFactory,
    UserState,
    TurnContext,
)
from microsoft_agents.hosting.dialogs import Dialog
from microsoft_agents.activity import ChannelAccount

from .dialog_agent import DialogAgent


class DialogAndWelcomeAgent(DialogAgent):
    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ):
        super().__init__(
            conversation_state, user_state, dialog
        )

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            # Greet anyone that was not the target (recipient) of this message.
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Welcome to Complex Dialog Bot {member.name}. This bot provides a complex conversation, with "
                        f"multiple dialogs. Type anything to get started. "
                    )
                )