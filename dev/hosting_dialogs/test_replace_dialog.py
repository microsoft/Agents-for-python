# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import ConversationState, MemoryStorage, TurnContext
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    DialogSet,
    DialogTurnStatus,
    WaterfallDialog,
)
from microsoft_agents.hosting.dialogs.models.dialog_instance import DialogInstance
from microsoft_agents.hosting.dialogs.models.dialog_reason import DialogReason
from microsoft_agents.hosting.dialogs.prompts import TextPrompt, PromptOptions
from tests.hosting_dialogs.helpers import DialogTestAdapter


def _text_prompt_options(text: str) -> PromptOptions:
    return PromptOptions(prompt=Activity(type=ActivityTypes.message, text=text))


class _WaterfallWithEndDialog(WaterfallDialog):
    """WaterfallDialog that announces itself when it ends."""

    async def end_dialog(
        self, context: TurnContext, instance: DialogInstance, reason: DialogReason
    ):
        await context.send_activity("*** WaterfallDialog End ***")
        await super().end_dialog(context, instance, reason)


class _SecondDialog(ComponentDialog):
    def __init__(self):
        super().__init__("SecondDialog")

        async def action_four(step):
            return await step.prompt("TextPrompt", _text_prompt_options("prompt four"))

        async def action_five(step):
            return await step.prompt("TextPrompt", _text_prompt_options("prompt five"))

        async def last_action(step):
            return await step.end_dialog()

        self.add_dialog(TextPrompt("TextPrompt"))
        self.add_dialog(
            WaterfallDialog("WaterfallDialog", [action_four, action_five, last_action])
        )
        self.initial_dialog_id = "WaterfallDialog"


class _FirstDialog(ComponentDialog):
    def __init__(self):
        super().__init__("FirstDialog")

        async def action_one(step):
            return await step.prompt("TextPrompt", _text_prompt_options("prompt one"))

        async def action_two(step):
            return await step.prompt("TextPrompt", _text_prompt_options("prompt two"))

        async def replace_action(step):
            if step.result == "replace":
                return await step.replace_dialog("SecondDialog")
            return await step.next(None)

        async def action_three(step):
            return await step.prompt("TextPrompt", _text_prompt_options("prompt three"))

        async def last_action(step):
            return await step.end_dialog()

        self.add_dialog(TextPrompt("TextPrompt"))
        self.add_dialog(_SecondDialog())
        self.add_dialog(
            _WaterfallWithEndDialog(
                "WaterfallWithEndDialog",
                [action_one, action_two, replace_action, action_three, last_action],
            )
        )
        self.initial_dialog_id = "WaterfallWithEndDialog"


class TestReplaceDialog:
    @pytest.mark.asyncio
    async def test_replace_dialog_no_branch(self):
        """Dialog flows through all three prompts without branching."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)
        ds.add(_FirstDialog())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("FirstDialog")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("prompt one")
        flow = await flow.send("hello")
        flow = await flow.assert_reply("prompt two")
        flow = await flow.send("hello")
        flow = await flow.assert_reply("prompt three")
        flow = await flow.send("hello")
        await flow.assert_reply("*** WaterfallDialog End ***")

    @pytest.mark.asyncio
    async def test_replace_dialog_branch(self):
        """Sending 'replace' causes replace_dialog to switch to SecondDialog."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)
        ds.add(_FirstDialog())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("FirstDialog")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("prompt one")
        flow = await flow.send("hello")
        flow = await flow.assert_reply("prompt two")
        flow = await flow.send("replace")
        flow = await flow.assert_reply("*** WaterfallDialog End ***")
        flow = await flow.assert_reply("prompt four")
        flow = await flow.send("hello")
        await flow.assert_reply("prompt five")
