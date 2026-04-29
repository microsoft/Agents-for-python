# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.dialogs import DialogSet, DialogTurnStatus
from microsoft_agents.hosting.core import MemoryStorage, ConversationState
from microsoft_agents.hosting.dialogs.prompts import (
    TextPrompt,
    PromptOptions,
    PromptValidatorContext,
)
from microsoft_agents.activity import Activity, ActivityTypes
from tests.hosting_dialogs.helpers import DialogTestAdapter


class TestPromptValidatorContext:

    @pytest.mark.asyncio
    async def test_prompt_validator_context_end(self):
        storage = MemoryStorage()
        conv = ConversationState(storage)
        accessor = conv.create_property("dialogstate")
        dialog_set = DialogSet(accessor)
        assert dialog_set is not None

    def test_prompt_validator_context_retry_end(self):
        storage = MemoryStorage()
        conv = ConversationState(storage)
        accessor = conv.create_property("dialogstate")
        dialog_set = DialogSet(accessor)
        assert dialog_set is not None

    @pytest.mark.asyncio
    async def test_attempt_count_starts_at_one_on_first_validation(self):
        """attempt_count is 1 on the first validator call and increments on each
        subsequent user reply (mirrors ActivityPrompt behaviour)."""
        observed_attempt_counts = []

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            observed_attempt_counts.append(pc.attempt_count)
            return bool(pc.recognized.value)

        ds.add(TextPrompt("TextPrompt", validator))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter text."),
                    retry_prompt=Activity(type=ActivityTypes.message, text="Again."),
                )
                await dc.prompt("TextPrompt", options)
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("hello")
        await flow.assert_reply("Enter text.")
        await adapter.send("something")

        assert observed_attempt_counts == [1]

    @pytest.mark.asyncio
    async def test_attempt_count_increments_across_retries(self):
        """attempt_count increments with each user reply, so retry #1 = 2, retry #2 = 3, etc."""
        observed_attempt_counts = []

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            observed_attempt_counts.append(pc.attempt_count)
            # Only accept the literal word "yes"
            return pc.recognized.succeeded and pc.recognized.value == "yes"

        ds.add(TextPrompt("TextPrompt", validator))

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Say yes."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message, text="Please say yes."
                    ),
                )
                await dc.prompt("TextPrompt", options)
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        flow = await adapter.send("start")
        await flow.assert_reply("Say yes.")
        await adapter.send("no")  # attempt 1 — rejected
        await adapter.send("nope")  # attempt 2 — rejected
        await adapter.send("yes")  # attempt 3 — accepted

        assert observed_attempt_counts == [1, 2, 3]
