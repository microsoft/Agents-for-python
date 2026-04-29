# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from typing import Callable

import pytest
from recognizers_text import Culture

from microsoft_agents.hosting.core import (
    TurnContext,
    ConversationState,
    MemoryStorage,
    MessageFactory,
)
from microsoft_agents.hosting.dialogs import DialogSet, DialogTurnStatus, DialogContext
from microsoft_agents.hosting.dialogs.prompts import (
    NumberPrompt,
    PromptOptions,
    PromptValidatorContext,
)
from microsoft_agents.activity import Activity, ActivityTypes
from tests.hosting_dialogs.helpers import DialogTestAdapter


class NumberPromptMock(NumberPrompt):
    def __init__(
        self,
        dialog_id: str,
        validator: Callable[[PromptValidatorContext], bool] = None,
        default_locale=None,
    ):
        super().__init__(dialog_id, validator, default_locale)

    async def on_prompt_null_context(self, options: PromptOptions):
        # Should throw TypeError
        await self.on_prompt(
            turn_context=None, state=None, options=options, is_retry=False
        )

    async def on_prompt_null_options(self, dialog_context: DialogContext):
        # Should throw TypeError
        await self.on_prompt(
            dialog_context.context, state=None, options=None, is_retry=False
        )

    async def on_recognize_null_context(self):
        # Should throw TypeError
        await self.on_recognize(turn_context=None, state=None, options=None)


class TestNumberPrompt:
    def test_empty_id_should_fail(self):
        empty_id = ""
        with pytest.raises(TypeError):
            NumberPrompt(empty_id)

    def test_none_id_should_fail(self):
        with pytest.raises(TypeError):
            NumberPrompt(dialog_id=None)

    @pytest.mark.asyncio
    async def test_with_null_turn_context_should_fail(self):
        number_prompt_mock = NumberPromptMock("NumberPromptMock")

        options = PromptOptions(
            prompt=Activity(type=ActivityTypes.message, text="Please send a number.")
        )

        with pytest.raises(TypeError):
            await number_prompt_mock.on_prompt_null_context(options)

    @pytest.mark.asyncio
    async def test_on_prompt_with_null_options_fails(self):
        conver_state = ConversationState(MemoryStorage())
        dialog_state = conver_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        number_prompt_mock = NumberPromptMock(
            dialog_id="NumberPromptMock", validator=None, default_locale=Culture.English
        )
        dialogs.add(number_prompt_mock)

        with pytest.raises(TypeError):
            await number_prompt_mock.on_recognize_null_context()

    @pytest.mark.asyncio
    async def test_number_prompt(self):
        # Create new ConversationState with MemoryStorage and register the state as middleware.
        conver_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the WaterfallDialog.
        dialog_state = conver_state.create_property("dialogState")

        dialogs = DialogSet(dialog_state)

        # Create and add number prompt to DialogSet.
        number_prompt = NumberPrompt("NumberPrompt", None, Culture.English)
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                await dialog_context.begin_dialog(
                    "NumberPrompt",
                    PromptOptions(
                        prompt=MessageFactory.text("Enter quantity of cable")
                    ),
                )
            else:
                if results.status == DialogTurnStatus.Complete:
                    number_result = results.result
                    await turn_context.send_activity(
                        MessageFactory.text(
                            f"You asked me for '{number_result}' meters of cable."
                        )
                    )

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply("Enter quantity of cable")
        step3 = await step2.send("Give me twenty meters of cable")
        await step3.assert_reply("You asked me for '20' meters of cable.")

    @pytest.mark.asyncio
    async def test_number_prompt_retry(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        number_prompt = NumberPrompt(
            dialog_id="NumberPrompt", validator=None, default_locale=Culture.English
        )
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context: DialogContext = await dialogs.create_context(turn_context)

            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message, text="You must enter a number."
                    ),
                )
                await dialog_context.prompt("NumberPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                number_result = results.result
                await turn_context.send_activity(
                    MessageFactory.text(f"Bot received the number '{number_result}'.")
                )

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Enter a number.")
        step3 = await step2.send("hello")
        step4 = await step3.assert_reply("You must enter a number.")
        step5 = await step4.send("64")
        await step5.assert_reply("Bot received the number '64'.")

    @pytest.mark.asyncio
    async def test_number_uses_locale_specified_in_constructor(self):
        # Create new ConversationState with MemoryStorage and register the state as middleware.
        conver_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the WaterfallDialog.
        dialog_state = conver_state.create_property("dialogState")

        dialogs = DialogSet(dialog_state)

        # Create and add number prompt to DialogSet.
        number_prompt = NumberPrompt(
            "NumberPrompt", None, default_locale=Culture.Spanish
        )
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                await dialog_context.begin_dialog(
                    "NumberPrompt",
                    PromptOptions(
                        prompt=MessageFactory.text(
                            "How much money is in your gaming account?"
                        )
                    ),
                )
            else:
                if results.status == DialogTurnStatus.Complete:
                    number_result = results.result
                    await turn_context.send_activity(
                        MessageFactory.text(
                            f"You say you have ${number_result} in your gaming account."
                        )
                    )

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply("How much money is in your gaming account?")
        step3 = await step2.send("I've got $1.200.555,42 in my account.")
        await step3.assert_reply("You say you have $1200555.42 in your gaming account.")

    @pytest.mark.asyncio
    async def test_number_prompt_validator(self):
        # Create new ConversationState with MemoryStorage and register the state as middleware.
        conver_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the WaterfallDialog.
        dialog_state = conver_state.create_property("dialogState")

        dialogs = DialogSet(dialog_state)

        # Create and add number prompt to DialogSet.
        async def validator(prompt_context: PromptValidatorContext):
            result = prompt_context.recognized.value

            if 0 < result < 100:
                return True

            return False

        number_prompt = NumberPrompt(
            "NumberPrompt", validator, default_locale=Culture.English
        )
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="You must enter a positive number less than 100.",
                    ),
                )
                await dialog_context.prompt("NumberPrompt", options)

            elif results.status == DialogTurnStatus.Complete:
                number_result = int(results.result)
                await turn_context.send_activity(
                    MessageFactory.text(f"Bot received the number '{number_result}'.")
                )

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Enter a number.")
        step3 = await step2.send("150")
        step4 = await step3.assert_reply(
            "You must enter a positive number less than 100."
        )
        step5 = await step4.send("64")
        await step5.assert_reply("Bot received the number '64'.")

    @pytest.mark.asyncio
    async def test_float_number_prompt(self):
        # Create new ConversationState with MemoryStorage and register the state as middleware.
        conver_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the WaterfallDialog.
        dialog_state = conver_state.create_property("dialogState")

        dialogs = DialogSet(dialog_state)

        # Create and add number prompt to DialogSet.
        number_prompt = NumberPrompt(
            "NumberPrompt", validator=None, default_locale=Culture.English
        )
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext) -> None:
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number.")
                )
                await dialog_context.prompt("NumberPrompt", options)

            elif results.status == DialogTurnStatus.Complete:
                number_result = float(results.result)
                await turn_context.send_activity(
                    MessageFactory.text(f"Bot received the number '{number_result}'.")
                )

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Enter a number.")
        step3 = await step2.send("3.14")
        await step3.assert_reply("Bot received the number '3.14'.")

    @pytest.mark.asyncio
    async def test_number_prompt_uses_locale_specified_in_activity(self):
        conver_state = ConversationState(MemoryStorage())
        dialog_state = conver_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        number_prompt = NumberPrompt("NumberPrompt", None, None)
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number.")
                )
                await dialog_context.prompt("NumberPrompt", options)

            elif results.status == DialogTurnStatus.Complete:
                number_result = float(results.result)
                assert 3.14 == number_result

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Enter a number.")
        await step2.send(
            Activity(type=ActivityTypes.message, text="3,14", locale=Culture.Spanish)
        )

    @pytest.mark.asyncio
    async def test_number_prompt_defaults_to_en_us_culture(self):
        conver_state = ConversationState(MemoryStorage())
        dialog_state = conver_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        number_prompt = NumberPrompt("NumberPrompt")
        dialogs.add(number_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Enter a number.")
                )
                await dialog_context.prompt("NumberPrompt", options)

            elif results.status == DialogTurnStatus.Complete:
                number_result = float(results.result)
                await turn_context.send_activity(
                    MessageFactory.text(f"Bot received the number '{number_result}'.")
                )

            await conver_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Enter a number.")
        step3 = await step2.send("3.14")
        await step3.assert_reply("Bot received the number '3.14'.")
