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
    async def test_attempt_count_is_zero_for_base_prompt_subclasses(self):
        """For Prompt subclasses (TextPrompt, NumberPrompt, etc.) the
        ATTEMPT_COUNT_KEY is never written to persisted state, so
        attempt_count is always 0 inside the validator regardless of how many
        times the user has been reprompted.

        This is a documented inconsistency with ActivityPrompt, which increments
        the counter before calling the validator (attempt_count >= 1).
        Use PromptOptions.number_of_attempts for reliable counting instead.
        """
        observed_attempt_counts = []

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def validator(pc: PromptValidatorContext) -> bool:
            observed_attempt_counts.append(pc.attempt_count)
            # Accept any non-empty text
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
        flow = await adapter.send("something")  # triggers validator

        # For Prompt subclasses, attempt_count is always 0 — the key is never stored
        assert all(
            count == 0 for count in observed_attempt_counts
        ), f"Expected all attempt_count=0 for base Prompt, got {observed_attempt_counts}"
