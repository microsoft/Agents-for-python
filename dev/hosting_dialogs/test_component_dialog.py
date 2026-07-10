# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import ConversationState, MemoryStorage
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    Dialog,
    DialogSet,
    DialogTurnResult,
    DialogTurnStatus,
    WaterfallDialog,
    WaterfallStepContext,
)
from microsoft_agents.hosting.dialogs.models.dialog_reason import DialogReason
from microsoft_agents.hosting.dialogs.prompts import NumberPrompt, PromptOptions
from tests.hosting_dialogs.helpers import DialogTestAdapter


def _number_prompt_options(text: str) -> PromptOptions:
    return PromptOptions(prompt=Activity(type=ActivityTypes.message, text=text))


class TestComponentDialog:
    @pytest.mark.asyncio
    async def test_begin_dialog_null_dc_raises(self):
        dialog = ComponentDialog("dialogId")
        with pytest.raises((TypeError, Exception)):
            await dialog.begin_dialog(None)

    @pytest.mark.asyncio
    async def test_basic_waterfall_with_number_prompt(self):
        """A two-step waterfall collects two numbers via NumberPrompt."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def step1(step):
            return await step.prompt(
                "number", _number_prompt_options("Enter a number.")
            )

        async def step2(step):
            await step.context.send_activity(f"Thanks for '{int(step.result)}'")
            return await step.prompt(
                "number", _number_prompt_options("Enter another number.")
            )

        ds.add(WaterfallDialog("test-waterfall", [step1, step2]))
        ds.add(NumberPrompt("number", default_locale="en-us"))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("test-waterfall")
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(
                    f"Bot received the number '{int(results.result)}'."
                )
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("42")
        flow = await flow.assert_reply("Thanks for '42'")
        flow = await flow.assert_reply("Enter another number.")
        flow = await flow.send("64")
        await flow.assert_reply("Bot received the number '64'.")

    @pytest.mark.asyncio
    async def test_basic_component_dialog(self):
        """ComponentDialog encapsulates its own waterfall and prompt."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        class TestComp(ComponentDialog):
            def __init__(self):
                super().__init__("TestComponentDialog")

                async def step1(step):
                    return await step.prompt(
                        "number", _number_prompt_options("Enter a number.")
                    )

                async def step2(step):
                    await step.context.send_activity(f"Thanks for '{int(step.result)}'")
                    return await step.prompt(
                        "number", _number_prompt_options("Enter another number.")
                    )

                self.add_dialog(WaterfallDialog("test-waterfall", [step1, step2]))
                self.add_dialog(NumberPrompt("number", default_locale="en-us"))

        ds.add(TestComp())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("TestComponentDialog")
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(
                    f"Bot received the number '{int(results.result)}'."
                )
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("42")
        flow = await flow.assert_reply("Thanks for '42'")
        flow = await flow.assert_reply("Enter another number.")
        flow = await flow.send("64")
        await flow.assert_reply("Bot received the number '64'.")

    @pytest.mark.asyncio
    async def test_call_dialog_in_parent_component(self):
        """A child component can call a dialog registered in its parent."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        child_component = ComponentDialog("childComponent")

        async def child_step1(step):
            await step.context.send_activity("Child started.")
            return await step.begin_dialog("parentDialog", "test")

        async def child_step2(step):
            await step.context.send_activity(f"Child finished. Value: {step.result}")
            return await step.end_dialog()

        child_component.add_dialog(
            WaterfallDialog("childDialog", [child_step1, child_step2])
        )

        parent_component = ComponentDialog("parentComponent")
        parent_component.add_dialog(child_component)

        async def parent_step(step):
            await step.context.send_activity("Parent called.")
            return await step.end_dialog(step.options)

        parent_component.add_dialog(WaterfallDialog("parentDialog", [parent_step]))
        ds.add(parent_component)

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("parentComponent")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("Hi")
        flow = await flow.assert_reply("Child started.")
        flow = await flow.assert_reply("Parent called.")
        await flow.assert_reply("Child finished. Value: test")

    @pytest.mark.asyncio
    async def test_call_dialog_defined_in_parent_component(self):
        """Child can call parent-registered dialog and receive the return value."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        options = {"value": "test"}

        child_component = ComponentDialog("childComponent")

        async def child_step1(step):
            await step.context.send_activity("Child started.")
            return await step.begin_dialog("parentDialog", options)

        async def child_step2(step):
            assert step.result == "test"
            await step.context.send_activity("Child finished.")
            return await step.end_dialog()

        child_component.add_dialog(
            WaterfallDialog("childDialog", [child_step1, child_step2])
        )

        parent_component = ComponentDialog("parentComponent")
        parent_component.add_dialog(child_component)

        async def parent_step(step):
            step_options = step.options
            await step.context.send_activity(
                f"Parent called with: {step_options['value']}"
            )
            return await step.end_dialog(step_options["value"])

        parent_component.add_dialog(WaterfallDialog("parentDialog", [parent_step]))
        ds.add(parent_component)

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("parentComponent")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("Hi")
        flow = await flow.assert_reply("Child started.")
        flow = await flow.assert_reply("Parent called with: test")
        await flow.assert_reply("Child finished.")

    @pytest.mark.asyncio
    async def test_nested_component_dialog(self):
        """Nested ComponentDialogs properly pass control between each other."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        class InnerComp(ComponentDialog):
            def __init__(self):
                super().__init__("TestComponentDialog")

                async def step1(step):
                    return await step.prompt(
                        "number", _number_prompt_options("Enter a number.")
                    )

                async def step2(step):
                    await step.context.send_activity(f"Thanks for '{int(step.result)}'")
                    return await step.prompt(
                        "number", _number_prompt_options("Enter another number.")
                    )

                self.add_dialog(WaterfallDialog("test-waterfall", [step1, step2]))
                self.add_dialog(NumberPrompt("number", default_locale="en-us"))

        class OuterComp(ComponentDialog):
            def __init__(self):
                super().__init__("TestNestedComponentDialog")

                async def step1(step):
                    return await step.prompt(
                        "number", _number_prompt_options("Enter a number.")
                    )

                async def step2(step):
                    await step.context.send_activity(f"Thanks for '{int(step.result)}'")
                    return await step.prompt(
                        "number", _number_prompt_options("Enter another number.")
                    )

                async def step3(step):
                    await step.context.send_activity(f"Got '{int(step.result)}'.")
                    return await step.begin_dialog("TestComponentDialog")

                self.add_dialog(
                    WaterfallDialog("test-waterfall", [step1, step2, step3])
                )
                self.add_dialog(NumberPrompt("number", default_locale="en-us"))
                self.add_dialog(InnerComp())

        ds.add(OuterComp())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("TestNestedComponentDialog")
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(
                    f"Bot received the number '{int(results.result)}'."
                )
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("42")
        flow = await flow.assert_reply("Thanks for '42'")
        flow = await flow.assert_reply("Enter another number.")
        flow = await flow.send("64")
        flow = await flow.assert_reply("Got '64'.")
        flow = await flow.assert_reply("Enter a number.")
        flow = await flow.send("101")
        flow = await flow.assert_reply("Thanks for '101'")
        flow = await flow.assert_reply("Enter another number.")
        flow = await flow.send("5")
        await flow.assert_reply("Bot received the number '5'.")


class TestComponentDialogOnEndDialogHook:
    @pytest.mark.asyncio
    async def test_on_end_dialog_called_with_cancel_reason(self):
        """on_end_dialog hook receives CancelCalled reason when cancel_all_dialogs() is invoked."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        hook_calls = []

        class TrackingComp(ComponentDialog):
            def __init__(self):
                super().__init__("TrackingComp")

                async def waiting_step(step):
                    return Dialog.end_of_turn

                self.add_dialog(WaterfallDialog("inner-wf", [waiting_step]))

            async def on_end_dialog(self, context, instance, reason):
                hook_calls.append(reason)

        ds.add(TrackingComp())

        turn = [0]

        async def exec(tc):
            turn[0] += 1
            dc = await ds.create_context(tc)
            if turn[0] == 1:
                results = await dc.continue_dialog()
                if results.status == DialogTurnStatus.Empty:
                    await dc.begin_dialog("TrackingComp")
            else:
                # Cancel without continuing so the waterfall doesn't advance
                await dc.cancel_all_dialogs()
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        await adapter.send("hi")  # starts the dialog, step 0 waits
        await adapter.send("cancel")  # triggers cancel_all_dialogs directly

        assert DialogReason.CancelCalled in hook_calls

    @pytest.mark.asyncio
    async def test_on_end_dialog_called_with_end_reason_on_completion(self):
        """on_end_dialog hook receives EndCalled reason when the component finishes normally."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        hook_calls = []

        class TrackingComp(ComponentDialog):
            def __init__(self):
                super().__init__("TrackingComp")

                async def ending_step(step):
                    return await step.end_dialog("done")

                self.add_dialog(WaterfallDialog("inner-wf", [ending_step]))

            async def on_end_dialog(self, context, instance, reason):
                hook_calls.append(reason)

        ds.add(TrackingComp())

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dc.begin_dialog("TrackingComp")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        await adapter.send("hi")  # starts and immediately completes the component

        assert DialogReason.EndCalled in hook_calls
