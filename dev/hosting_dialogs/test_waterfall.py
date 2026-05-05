# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from recognizers_text import Culture

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import ConversationState, MemoryStorage, TurnContext
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    Dialog,
    DialogSet,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    DialogTurnStatus,
)
from microsoft_agents.hosting.dialogs.prompts import (
    NumberPrompt,
    DateTimePrompt,
    PromptOptions,
)
from tests.hosting_dialogs.helpers import DialogTestAdapter


class TestWaterfallDialog:
    def test_waterfall_none_name(self):
        with pytest.raises((TypeError, Exception)):
            WaterfallDialog(None)

    def test_waterfall_add_none_step(self):
        waterfall = WaterfallDialog("test")
        with pytest.raises((TypeError, Exception)):
            waterfall.add_step(None)

    def test_waterfall_with_set_instead_of_array(self):
        with pytest.raises((TypeError, Exception)):
            WaterfallDialog("a", {1, 2})

    @pytest.mark.asyncio
    async def test_execute_sequence_waterfall_steps(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        async def step1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("bot responding.")
            return Dialog.end_of_turn

        async def step2(step: WaterfallStepContext) -> DialogTurnResult:
            return await step.end_dialog("ending WaterfallDialog.")

        my_dialog = WaterfallDialog("test", [step1, step2])
        dialogs.add(my_dialog)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dialog_context.begin_dialog("test")
            else:
                if results.status == DialogTurnStatus.Complete:
                    await turn_context.send_activity(results.result)
            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1_flow = await adapter.send("begin")
        step2_flow = await step1_flow.assert_reply("bot responding.")
        step3_flow = await step2_flow.send("continue")
        await step3_flow.assert_reply("ending WaterfallDialog.")

    def test_waterfall_callback(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        async def step_callback1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step1")

        async def step_callback2(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step2")

        async def step_callback3(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step3")

        steps = [step_callback1, step_callback2, step_callback3]
        dialogs.add(WaterfallDialog("test", steps))
        assert dialogs is not None
        assert len(dialogs._dialogs) == 1  # pylint: disable=protected-access

    def test_waterfall_with_class(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        class MyWaterfallDialog(WaterfallDialog):
            def __init__(self, dialog_id: str):
                async def step1(step: WaterfallStepContext) -> DialogTurnResult:
                    await step.context.send_activity("step1")
                    return Dialog.end_of_turn

                async def step2(step: WaterfallStepContext) -> DialogTurnResult:
                    await step.context.send_activity("step2")
                    return Dialog.end_of_turn

                super().__init__(dialog_id, [step1, step2])

        dialogs.add(MyWaterfallDialog("test"))
        assert dialogs is not None
        assert len(dialogs._dialogs) == 1  # pylint: disable=protected-access

    @pytest.mark.asyncio
    async def test_waterfall_step_parent_is_waterfall_parent(self):
        """WaterfallStepContext.parent should be the ComponentDialog containing the waterfall."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")

        result_holder = {}

        class WaterfallParentDialog(ComponentDialog):
            def __init__(self):
                super().__init__("waterfall-parent-test-dialog")

                async def step1(step: WaterfallStepContext) -> DialogTurnResult:
                    # Parent context should have the component dialog as its active dialog
                    parent_id = (
                        step.parent.active_dialog.id
                        if step.parent and step.parent.active_dialog
                        else None
                    )
                    result_holder["parent_id"] = parent_id
                    await step.context.send_activity("verified")
                    return Dialog.end_of_turn

                self.add_dialog(WaterfallDialog("test", [step1]))
                self.initial_dialog_id = "test"

        ds = DialogSet(dialog_state)
        ds.add(WaterfallParentDialog())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("waterfall-parent-test-dialog")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        await flow.assert_reply("verified")

        assert result_holder.get("parent_id") == "waterfall-parent-test-dialog"

    @pytest.mark.asyncio
    async def test_waterfall_prompt(self):
        """Waterfall with NumberPrompt: invalid inputs trigger retry, valid inputs advance steps."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")

        async def step1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step1")
            return await step.prompt(
                "number",
                PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message, text="It must be a number"
                    ),
                ),
            )

        async def step2(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity(f"Thanks for '{int(step.result)}'")
            await step.context.send_activity("step2")
            return await step.prompt(
                "number",
                PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message, text="It must be a number"
                    ),
                ),
            )

        async def step3(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity(f"Thanks for '{int(step.result)}'")
            await step.context.send_activity("step3")
            return await step.end_dialog()

        ds = DialogSet(dialog_state)
        ds.add(WaterfallDialog("test-waterfall", [step1, step2, step3]))
        ds.add(NumberPrompt("number", default_locale=Culture.English))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("test-waterfall")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("step1")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("hello again")
        flow = await flow.assert_reply("It must be a number")
        flow = await flow.send("42")
        flow = await flow.assert_reply("Thanks for '42'")
        flow = await flow.assert_reply("step2")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("apple")
        flow = await flow.assert_reply("It must be a number")
        flow = await flow.send("orange")
        flow = await flow.assert_reply("It must be a number")
        flow = await flow.send("64")
        flow = await flow.assert_reply("Thanks for '64'")
        await flow.assert_reply("step3")

    @pytest.mark.asyncio
    async def test_waterfall_nested(self):
        """Nested waterfall dialogs chain correctly when each ends."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")

        async def waterfall_a_step1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step1")
            return await step.begin_dialog("test-waterfall-b")

        async def waterfall_a_step2(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step2")
            return await step.begin_dialog("test-waterfall-c")

        async def waterfall_b_step1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step1.1")
            return Dialog.end_of_turn

        async def waterfall_b_step2(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step1.2")
            return Dialog.end_of_turn

        async def waterfall_c_step1(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step2.1")
            return Dialog.end_of_turn

        async def waterfall_c_step2(step: WaterfallStepContext) -> DialogTurnResult:
            await step.context.send_activity("step2.2")
            return await step.end_dialog()

        ds = DialogSet(dialog_state)
        ds.add(
            WaterfallDialog("test-waterfall-a", [waterfall_a_step1, waterfall_a_step2])
        )
        ds.add(
            WaterfallDialog("test-waterfall-b", [waterfall_b_step1, waterfall_b_step2])
        )
        ds.add(
            WaterfallDialog("test-waterfall-c", [waterfall_c_step1, waterfall_c_step2])
        )

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("test-waterfall-a")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("step1")
        flow = await flow.assert_reply("step1.1")
        flow = await flow.send("hello")
        flow = await flow.assert_reply("step1.2")
        flow = await flow.send("hello")
        flow = await flow.assert_reply("step2")
        flow = await flow.assert_reply("step2.1")
        flow = await flow.send("hello")
        await flow.assert_reply("step2.2")

    @pytest.mark.asyncio
    async def test_waterfall_datetime_prompt_first_invalid_then_valid(self):
        """DateTimePrompt re-prompts on invalid input and accepts valid date/time."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")

        async def step1(step: WaterfallStepContext) -> DialogTurnResult:
            return await step.prompt(
                "dateTimePrompt",
                PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Provide a date")
                ),
            )

        async def step2(step: WaterfallStepContext) -> DialogTurnResult:
            assert step.result is not None
            return await step.end_dialog()

        ds = DialogSet(dialog_state)
        ds.add(DateTimePrompt("dateTimePrompt", default_locale=Culture.English))
        ds.add(WaterfallDialog("test-dateTimePrompt", [step1, step2]))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("test-dateTimePrompt")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Provide a date")
        flow = await flow.send("hello again")
        flow = await flow.assert_reply("Provide a date")
        await flow.send("Wednesday 4 oclock")
