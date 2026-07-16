# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# pylint: disable=pointless-string-statement

from enum import Enum
from typing import Callable, List, Tuple

import pytest

from microsoft_agents.hosting.core import (
    ConversationState,
    MemoryStorage,
    MessageFactory,
    UserState,
    TurnContext,
)
from microsoft_agents.hosting.core import ClaimsIdentity
from microsoft_agents.hosting.core.authorization import AuthenticationConstants
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    Dialog,
    DialogContext,
    DialogEvents,
    DialogInstance,
    DialogReason,
    TextPrompt,
    WaterfallDialog,
    DialogManager,
    DialogManagerResult,
    DialogTurnStatus,
    WaterfallStepContext,
)
from microsoft_agents.hosting.dialogs.prompts import PromptOptions
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    EndOfConversationCodes,
    InputHints,
    Channels,
)
from tests.hosting_dialogs.helpers import DialogTestAdapter


class SkillFlowTestCase(str, Enum):
    # DialogManager is executing on a root bot with no skills (typical standalone bot).
    root_bot_only = "RootBotOnly"

    # DialogManager is executing on a root bot handling replies from a skill.
    root_bot_consuming_skill = "RootBotConsumingSkill"

    # DialogManager is executing in a skill that is called from a root and calling another skill.
    middle_skill = "MiddleSkill"

    # DialogManager is executing in a skill that is called from a parent (a root or another skill) but doesn't call
    # another skill.
    leaf_skill = "LeafSkill"


class SimpleComponentDialog(ComponentDialog):
    # An App ID for a parent bot.
    parent_bot_id = "00000000-0000-0000-0000-0000000000PARENT"

    # An App ID for a skill bot.
    skill_bot_id = "00000000-0000-0000-0000-00000000000SKILL"

    # Captures an EndOfConversation if it was sent to help with assertions.
    eoc_sent: Activity = None

    # Property to capture the DialogManager turn results and do assertions.
    dm_turn_result: DialogManagerResult = None

    def __init__(
        self, id: str = None, prop: str = None
    ):  # pylint: disable=unused-argument
        super().__init__(id or "SimpleComponentDialog")
        self.text_prompt = "TextPrompt"
        self.waterfall_dialog = "WaterfallDialog"
        self.add_dialog(TextPrompt(self.text_prompt))
        self.add_dialog(
            WaterfallDialog(
                self.waterfall_dialog,
                [
                    self.prompt_for_name,
                    self.final_step,
                ],
            )
        )
        self.initial_dialog_id = self.waterfall_dialog
        self.end_reason = None

    @staticmethod
    async def create_test_flow(
        dialog: Dialog,
        test_case: SkillFlowTestCase = SkillFlowTestCase.root_bot_only,
        enabled_trace=False,
    ) -> DialogTestAdapter:
        conversation_id = "testFlowConversationId"
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        user_state = UserState(storage)

        activity = Activity(
            type=ActivityTypes.message,
            channel_id=Channels.test,
            service_url="https://test.com",
            from_property=ChannelAccount(id="user1", name="User1"),
            recipient=ChannelAccount(id="bot", name="Bot"),
            conversation=ConversationAccount(
                is_group=False, conversation_type=conversation_id, id=conversation_id
            ),
        )

        dialog_manager = DialogManager(dialog)
        dialog_manager.user_state = user_state
        dialog_manager.conversation_state = conversation_state

        async def logic(context: TurnContext):
            if test_case != SkillFlowTestCase.root_bot_only:
                # Create a skill ClaimsIdentity and put it in turn_state so isSkillClaim() returns True.
                claims_identity = ClaimsIdentity({}, False)
                claims_identity.claims["ver"] = (
                    "2.0"  # AuthenticationConstants.VersionClaim
                )
                claims_identity.claims["aud"] = (
                    SimpleComponentDialog.skill_bot_id
                )  # AuthenticationConstants.AudienceClaim
                claims_identity.claims["azp"] = (
                    SimpleComponentDialog.parent_bot_id
                )  # AuthenticationConstants.AuthorizedParty
                context._identity = claims_identity

                # Note: SkillHandler.SKILL_CONVERSATION_REFERENCE_KEY based skill routing
                # is not available in the new SDK. Skill flow test cases that require it are skipped.

            async def aux(
                turn_context: TurnContext,  # pylint: disable=unused-argument
                activities: List[Activity],
                next: Callable,
            ):
                for activity in activities:
                    if activity.type == ActivityTypes.end_of_conversation:
                        SimpleComponentDialog.eoc_sent = activity
                        break

                return await next()

            # Interceptor to capture the EoC activity if it was sent so we can assert it in the tests.
            context.on_send_activities(aux)

            SimpleComponentDialog.dm_turn_result = await dialog_manager.on_turn(context)

            # Manually save state since AutoSaveStateMiddleware is not available
            await conversation_state.save(context)
            await user_state.save(context)

        adapter = DialogTestAdapter(logic)
        if enabled_trace:
            adapter.enable_trace = True

        return adapter

    async def on_end_dialog(
        self, context: DialogContext, instance: DialogInstance, reason: DialogReason
    ):
        self.end_reason = reason
        return await super().on_end_dialog(context, instance, reason)

    async def prompt_for_name(self, step: WaterfallStepContext):
        return await step.prompt(
            self.text_prompt,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Hello, what is your name?", None, InputHints.expecting_input
                ),
                retry_prompt=MessageFactory.text(
                    "Hello, what is your name again?", None, InputHints.expecting_input
                ),
            ),
        )

    async def final_step(self, step: WaterfallStepContext):
        await step.context.send_activity(f"Hello { step.result }, nice to meet you!")
        return await step.end_dialog(step.result)


class TestDialogManager:
    @pytest.mark.asyncio
    async def test_handles_root_bot_only(self):
        SimpleComponentDialog.dm_turn_result = None
        SimpleComponentDialog.eoc_sent = None
        dialog = SimpleComponentDialog()
        test_flow = await SimpleComponentDialog.create_test_flow(
            dialog, SkillFlowTestCase.root_bot_only
        )
        step1 = await test_flow.send("Hi")
        step2 = await step1.assert_reply("Hello, what is your name?")
        step3 = await step2.send("SomeName")
        await step3.assert_reply("Hello SomeName, nice to meet you!")

        assert (
            SimpleComponentDialog.dm_turn_result.turn_result.status
            == DialogTurnStatus.Complete
        )
        assert dialog.end_reason == DialogReason.EndCalled
        assert (
            SimpleComponentDialog.eoc_sent is None
        ), "Root bot should not send EndConversation to channel"

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_root_bot_consuming_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_middle_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_handles_leaf_skill(self):
        pass

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_skill_handles_eoc_from_parent(self):
        pass

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_skill_handles_reprompt_from_parent(self):
        pass

    @pytest.mark.skip(
        reason="Requires SkillHandler/SkillConversationReference skill infrastructure not available in new SDK"
    )
    @pytest.mark.asyncio
    async def test_skill_should_return_empty_on_reprompt_with_no_dialog(self):
        pass

    @pytest.mark.asyncio
    async def test_trace_bot_state(self):
        SimpleComponentDialog.dm_turn_result = None
        dialog = SimpleComponentDialog()

        def assert_is_trace(activity, description):  # pylint: disable=unused-argument
            assert activity.type == ActivityTypes.trace
            return True

        def assert_is_trace_and_label(activity, description):
            assert_is_trace(activity, description)
            assert activity.label == "Bot State"
            return True

        test_flow = await SimpleComponentDialog.create_test_flow(
            dialog, SkillFlowTestCase.root_bot_only, True
        )

        step1 = await test_flow.send("Hi")
        step2 = await step1.assert_reply("Hello, what is your name?")
        step3 = await step2.assert_reply(assert_is_trace_and_label)
        step4 = await step3.send("SomeName")
        step5 = await step4.assert_reply("Hello SomeName, nice to meet you!")
        await step5.assert_reply(assert_is_trace_and_label)

        assert (
            SimpleComponentDialog.dm_turn_result.turn_result.status
            == DialogTurnStatus.Complete
        )
