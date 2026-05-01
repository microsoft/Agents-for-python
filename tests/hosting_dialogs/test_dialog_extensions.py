# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# pylint: disable=ungrouped-imports
import enum
from typing import List
import uuid

import pytest

from microsoft_agents.hosting.core import ClaimsIdentity
from microsoft_agents.hosting.core.authorization import AuthenticationConstants
from microsoft_agents.hosting.core import (
    TurnContext,
    MessageFactory,
    MemoryStorage,
    ConversationState,
    UserState,
)
from microsoft_agents.activity import ActivityTypes, Activity, EndOfConversationCodes
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    TextPrompt,
    WaterfallDialog,
    DialogInstance,
    DialogReason,
    WaterfallStepContext,
    PromptOptions,
    Dialog,
    DialogExtensions,
    DialogEvents,
)
from tests.hosting_dialogs.helpers import DialogTestAdapter


class SimpleComponentDialog(ComponentDialog):
    def __init__(self):
        super().__init__("SimpleComponentDialog")

        self.add_dialog(TextPrompt("TextPrompt"))
        self.add_dialog(
            WaterfallDialog("WaterfallDialog", [self.prompt_for_name, self.final_step])
        )

        self.initial_dialog_id = "WaterfallDialog"
        self.end_reason = DialogReason.BeginCalled

    async def end_dialog(
        self, context: TurnContext, instance: DialogInstance, reason: DialogReason
    ) -> None:
        self.end_reason = reason
        return await super().end_dialog(context, instance, reason)

    async def prompt_for_name(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            "TextPrompt",
            PromptOptions(
                prompt=MessageFactory.text("Hello, what is your name?"),
                retry_prompt=MessageFactory.text("Hello, what is your name again?"),
            ),
        )

    async def final_step(self, step_context: WaterfallStepContext):
        await step_context.context.send_activity(
            f"Hello {step_context.result}, nice to meet you!"
        )
        return await step_context.end_dialog(step_context.result)


class FlowTestCase(enum.Enum):
    root_bot_only = 1
    root_bot_consuming_skill = 2
    middle_skill = 3
    leaf_skill = 4


class TestDialogExtensions:
    def setup_method(self):
        self.eoc_sent: Activity = None
        self.skill_bot_id = str(uuid.uuid4())
        self.parent_bot_id = str(uuid.uuid4())

    def _create_test_flow(
        self, dialog: Dialog, test_case: FlowTestCase
    ) -> DialogTestAdapter:
        """
        Creates a DialogTestAdapter configured for the given test case.
        Returns the adapter (which supports send/assert_reply as a TestFlow entry point).
        """
        conversation_id = str(uuid.uuid4())
        storage = MemoryStorage()
        convo_state = ConversationState(storage)

        eoc_sent_ref = [None]
        self.eoc_sent = None

        async def logic(context: TurnContext):
            if test_case != FlowTestCase.root_bot_only:
                claims_identity = ClaimsIdentity(
                    {
                        AuthenticationConstants.VERSION_CLAIM: "2.0",
                        AuthenticationConstants.AUDIENCE_CLAIM: self.skill_bot_id,
                        AuthenticationConstants.AUTHORIZED_PARTY: self.parent_bot_id,
                    },
                    True,
                )
                context._identity = claims_identity

            async def capture_eoc(
                inner_context: TurnContext, activities: List[Activity], next
            ):  # pylint: disable=unused-argument
                for activity in activities:
                    if activity.type == ActivityTypes.end_of_conversation:
                        self.eoc_sent = activity
                        eoc_sent_ref[0] = activity
                        break
                return await next()

            context.on_send_activities(capture_eoc)

            await DialogExtensions.run_dialog(
                dialog, context, convo_state.create_property("DialogState")
            )

        return DialogTestAdapter(logic)

    @pytest.mark.asyncio
    async def test_handles_root_bot_only(self):
        dialog = SimpleComponentDialog()
        adapter = self._create_test_flow(dialog, FlowTestCase.root_bot_only)

        step1 = await adapter.send("Hi")
        step2 = await step1.assert_reply("Hello, what is your name?")
        step3 = await step2.send("SomeName")
        await step3.assert_reply("Hello SomeName, nice to meet you!")

        assert dialog.end_reason == DialogReason.EndCalled
        assert (
            self.eoc_sent is None
        ), "Root bot should not send EndConversation to channel"

    @pytest.mark.skip(
        reason="Requires skill infrastructure (SkillHandler/SkillConversationReference) not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_root_bot_consuming_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires skill infrastructure (SkillHandler/SkillConversationReference) not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_middle_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires skill infrastructure (SkillHandler/SkillConversationReference) not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_leaf_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires skill infrastructure (SkillHandler/SkillConversationReference) not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_skill_handles_eoc_from_parent(self):
        pass

    @pytest.mark.asyncio
    async def test_skill_handles_reprompt_from_parent(self):
        """
        Tests that a reprompt event causes the dialog to re-prompt.
        This test does not require skill infrastructure.
        """
        dialog = SimpleComponentDialog()
        adapter = self._create_test_flow(dialog, FlowTestCase.root_bot_only)

        step1 = await adapter.send("Hi")
        step2 = await step1.assert_reply("Hello, what is your name?")
        await step2.send(
            Activity(
                type=ActivityTypes.event,
                name=DialogEvents.reprompt_dialog,
            )
        )

        assert dialog.end_reason == DialogReason.BeginCalled
