# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import ConversationState, MemoryStorage
from microsoft_agents.hosting.dialogs import DialogSet, DialogTurnStatus
from microsoft_agents.hosting.dialogs.prompts import (
    TextPrompt,
    PromptOptions,
    PromptValidatorContext,
)
from tests.hosting_dialogs.helpers import DialogTestAdapter


class TestTextPrompt:
    def test_empty_id_raises(self):
        with pytest.raises((TypeError, Exception)):
            TextPrompt("")

    def test_null_id_raises(self):
        with pytest.raises((TypeError, Exception)):
            TextPrompt(None)

    @pytest.mark.asyncio
    async def test_basic_text_prompt(self):
        """TextPrompt echoes user input back after the prompt."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)
        ds.add(TextPrompt("TextPrompt"))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter some text.")
                )
                await dc.prompt("TextPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(f"Bot received: {results.result}")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter some text.")
        flow = await flow.send("some text")
        await flow.assert_reply("Bot received: some text")

    @pytest.mark.asyncio
    async def test_text_prompt_with_validator(self):
        """A validator can reject short inputs and trigger the retry prompt."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            return pc.recognized.value is not None and len(pc.recognized.value) > 3

        ds.add(TextPrompt("TextPrompt", validator))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Enter some text."
                    ),
                    retry_prompt=Activity(
                        type=ActivityTypes.message, text="That's not long enough."
                    ),
                )
                await dc.prompt("TextPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(f"Bot received: {results.result}")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter some text.")
        flow = await flow.send("hi")  # Too short — validator rejects
        flow = await flow.assert_reply("That's not long enough.")
        flow = await flow.send("hello world")  # Long enough
        await flow.assert_reply("Bot received: hello world")

    @pytest.mark.asyncio
    async def test_text_prompt_retry_on_failed_validation(self):
        """Without a retry_prompt the original prompt is re-sent on failure."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            return pc.recognized.value is not None and pc.recognized.value != "bad"

        ds.add(TextPrompt("TextPrompt", validator))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Enter something."
                    ),
                )
                await dc.prompt("TextPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(f"Got: {results.result}")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter something.")
        flow = await flow.send("bad")  # Rejected by validator
        flow = await flow.assert_reply("Enter something.")  # Re-prompted
        flow = await flow.send("good")
        await flow.assert_reply("Got: good")

    @pytest.mark.asyncio
    async def test_text_prompt_non_message_activity_does_not_succeed(self):
        """A non-message activity (e.g. event) causes recognition to fail.

        The base Prompt.continue_dialog returns end_of_turn immediately for
        non-message activities without calling the recognizer or validator.
        The dialog remains active (Waiting) and the user is not re-prompted.
        """
        from microsoft_agents.activity import ActivityTypes

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)
        ds.add(TextPrompt("TextPrompt"))

        completed = []

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter something.")
                )
                await dc.prompt("TextPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                completed.append(results.result)
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        # Start the prompt
        flow = await adapter.send("hello")
        await flow.assert_reply("Enter something.")

        # Send a non-message event — dialog must NOT complete
        event_activity = Activity(type=ActivityTypes.event, name="custom")
        await adapter.process_activity_async(event_activity, exec)
        assert len(completed) == 0, "Prompt must not complete on non-message activity"

    @pytest.mark.asyncio
    async def test_text_prompt_with_custom_message_validator(self):
        """Validator can send its own message and return False."""
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            if pc.recognized.value and len(pc.recognized.value) > 5:
                return True
            await pc.context.send_activity("Please enter more than 5 characters.")
            return False

        ds.add(TextPrompt("TextPrompt", validator))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter text."),
                )
                await dc.prompt("TextPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                await tc.send_activity(f"Done: {results.result}")
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        flow = await flow.assert_reply("Enter text.")
        flow = await flow.send("hi")
        flow = await flow.assert_reply("Please enter more than 5 characters.")
        flow = await flow.send("hello world")
        await flow.assert_reply("Done: hello world")
