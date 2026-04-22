# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.dialogs.prompts import DateTimePrompt, PromptOptions
from microsoft_agents.hosting.core import (
    MessageFactory,
    ConversationState,
    MemoryStorage,
    TurnContext,
)
from microsoft_agents.hosting.dialogs import DialogSet, DialogTurnStatus
from tests.hosting_dialogs.helpers import DialogTestAdapter


class TestDatetimePrompt:
    @pytest.mark.asyncio
    async def test_date_time_prompt(self):
        # Create new ConversationState with MemoryStorage and register the state as middleware.
        conver_state = ConversationState(MemoryStorage())

        # Create a DialogState property
        dialog_state = conver_state.create_property("dialogState")

        # Create new DialogSet.
        dialogs = DialogSet(dialog_state)

        # Create and add DateTime prompt to DialogSet.
        date_time_prompt = DateTimePrompt("DateTimePrompt")
        dialogs.add(date_time_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            prompt_msg = "What date would you like?"
            dialog_context = await dialogs.create_context(turn_context)

            results = await dialog_context.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(prompt=MessageFactory.text(prompt_msg))
                await dialog_context.begin_dialog("DateTimePrompt", options)
            else:
                if results.status == DialogTurnStatus.Complete:
                    resolution = results.result[0]
                    reply = MessageFactory.text(
                        f"Timex: '{resolution.timex}' Value: '{resolution.value}'"
                    )
                    await turn_context.send_activity(reply)
            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("What date would you like?")
        step3 = await step2.send("5th December 2018 at 9am")
        await step3.assert_reply("Timex: '2018-12-05T09' Value: '2018-12-05 09:00:00'")

    @pytest.mark.asyncio
    async def test_date_time_prompt_retry_on_invalid_input(self):
        """DateTimePrompt sends the retry_prompt when input cannot be recognized, then accepts valid input."""
        conver_state = ConversationState(MemoryStorage())
        dialog_state = conver_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        dialogs.add(DateTimePrompt("DateTimePrompt"))

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=MessageFactory.text("What date?"),
                    retry_prompt=MessageFactory.text("Not a valid date. Try again."),
                )
                await dialog_context.begin_dialog("DateTimePrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                resolution = results.result[0]
                await turn_context.send_activity(
                    MessageFactory.text(f"Timex: '{resolution.timex}'")
                )
            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("What date?")
        step3 = await step2.send("not a date at all xyz")
        step4 = await step3.assert_reply("Not a valid date. Try again.")
        step5 = await step4.send("5th December 2018")
        await step5.assert_reply("Timex: '2018-12-05'")
