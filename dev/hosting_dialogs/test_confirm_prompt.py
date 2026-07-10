# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List

import pytest

from microsoft_agents.hosting.core import (
    ConversationState,
    MemoryStorage,
    TurnContext,
    MessageFactory,
)
from microsoft_agents.hosting.dialogs import (
    DialogSet,
    DialogTurnResult,
    DialogTurnStatus,
)
from microsoft_agents.hosting.dialogs.choices import (
    Choice,
    ChoiceFactoryOptions,
    ListStyle,
)
from microsoft_agents.hosting.dialogs.prompts import (
    ConfirmPrompt,
    PromptCultureModel,
    PromptOptions,
    PromptValidatorContext,
)
from microsoft_agents.activity import Activity, ActivityTypes
from tests.hosting_dialogs.helpers import DialogTestAdapter


class TestConfirmPrompt:
    def test_confirm_prompt_with_empty_id_should_fail(self):
        empty_id = ""

        with pytest.raises(TypeError):
            ConfirmPrompt(empty_id)

    def test_confirm_prompt_with_none_id_should_fail(self):
        none_id = None

        with pytest.raises(TypeError):
            ConfirmPrompt(none_id)

    @pytest.mark.asyncio
    async def test_confirm_prompt(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm.")
                )
                await dialog_context.prompt("ConfirmPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Please confirm. (1) Yes or (2) No")
        step3 = await step2.send("yes")
        await step3.assert_reply("Confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_retry(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please confirm, say 'yes' or 'no' or something like that.",
                    ),
                )
                await dialog_context.prompt("ConfirmPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Please confirm. (1) Yes or (2) No")
        step3 = await step2.send("lala")
        step4 = await step3.assert_reply(
            "Please confirm, say 'yes' or 'no' or something like that. (1) Yes or (2) No"
        )
        step5 = await step4.send("no")
        await step5.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_no_options(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                await dialog_context.prompt("ConfirmPrompt", PromptOptions())
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply(" (1) Yes or (2) No")
        step3 = await step2.send("lala")
        step4 = await step3.assert_reply(" (1) Yes or (2) No")
        step5 = await step4.send("no")
        await step5.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_choice_options_numbers(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        confirm_prompt.choice_options = ChoiceFactoryOptions(include_numbers=True)
        confirm_prompt.style = ListStyle.in_line
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please confirm, say 'yes' or 'no' or something like that.",
                    ),
                )
                await dialog_context.prompt("ConfirmPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Please confirm. (1) Yes or (2) No")
        step3 = await step2.send("lala")
        step4 = await step3.assert_reply(
            "Please confirm, say 'yes' or 'no' or something like that. (1) Yes or (2) No"
        )
        step5 = await step4.send("2")
        await step5.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_choice_options_multiple_attempts(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        confirm_prompt.choice_options = ChoiceFactoryOptions(include_numbers=True)
        confirm_prompt.style = ListStyle.in_line
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please confirm, say 'yes' or 'no' or something like that.",
                    ),
                )
                await dialog_context.prompt("ConfirmPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Please confirm. (1) Yes or (2) No")
        step3 = await step2.send("lala")
        step4 = await step3.assert_reply(
            "Please confirm, say 'yes' or 'no' or something like that. (1) Yes or (2) No"
        )
        step5 = await step4.send("what")
        step6 = await step5.assert_reply(
            "Please confirm, say 'yes' or 'no' or something like that. (1) Yes or (2) No"
        )
        step7 = await step6.send("2")
        await step7.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_options_no_numbers(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        confirm_prompt = ConfirmPrompt("ConfirmPrompt", default_locale="English")
        confirm_prompt.choice_options = ChoiceFactoryOptions(
            include_numbers=False, inline_separator="~"
        )
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm."),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please confirm, say 'yes' or 'no' or something like that.",
                    ),
                )
                await dialog_context.prompt("ConfirmPrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                message_text = "Confirmed" if results.result else "Not confirmed"
                await turn_context.send_activity(MessageFactory.text(message_text))

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply("Please confirm. Yes or No")
        step3 = await step2.send("2")
        step4 = await step3.assert_reply(
            "Please confirm, say 'yes' or 'no' or something like that. Yes or No"
        )
        step5 = await step4.send("no")
        await step5.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_confirm_prompt_should_default_to_english_locale(self):
        locales = [None, "", "not-supported"]

        for locale in locales:
            convo_state = ConversationState(MemoryStorage())
            dialog_state = convo_state.create_property("dialogState")
            dialogs = DialogSet(dialog_state)
            confirm_prompt = ConfirmPrompt("ConfirmPrompt")
            confirm_prompt.choice_options = ChoiceFactoryOptions(include_numbers=True)
            dialogs.add(confirm_prompt)

            async def exec_test(turn_context: TurnContext):
                dialog_context = await dialogs.create_context(turn_context)

                results: DialogTurnResult = await dialog_context.continue_dialog()

                if results.status == DialogTurnStatus.Empty:
                    options = PromptOptions(
                        prompt=Activity(
                            type=ActivityTypes.message, text="Please confirm."
                        ),
                        retry_prompt=Activity(
                            type=ActivityTypes.message,
                            text="Please confirm, say 'yes' or 'no' or something like that.",
                        ),
                    )
                    await dialog_context.prompt("ConfirmPrompt", options)
                elif results.status == DialogTurnStatus.Complete:
                    message_text = "Confirmed" if results.result else "Not confirmed"
                    await turn_context.send_activity(MessageFactory.text(message_text))

                await convo_state.save(turn_context)

            adapter = DialogTestAdapter(exec_test)

            # Activity.locale uses NonEmptyString which rejects None/""; use model_construct to bypass
            send_activity = Activity.model_construct(
                type=ActivityTypes.message, text="Hello", locale=locale or None
            )
            step1 = await adapter.send(send_activity)
            step2 = await step1.assert_reply("Please confirm. (1) Yes or (2) No")
            step3 = await step2.send("lala")
            step4 = await step3.assert_reply(
                "Please confirm, say 'yes' or 'no' or something like that. (1) Yes or (2) No"
            )
            step5 = await step4.send("2")
            await step5.assert_reply("Not confirmed")

    @pytest.mark.asyncio
    async def test_should_recognize_locale_variations_of_correct_locales(self):
        def cap_ending(locale: str) -> str:
            return f"{locale.split('-')[0]}-{locale.split('-')[1].upper()}"

        def title_ending(locale: str) -> str:
            return locale[:3] + locale[3].upper() + locale[4:]

        def cap_two_letter(locale: str) -> str:
            return locale.split("-")[0].upper()

        def lower_two_letter(locale: str) -> str:
            return locale.split("-")[0].upper()

        async def exec_test_for_locale(valid_locale: str, locale_variations: List):
            # Hold the correct answer from when a valid locale is used
            expected_answer = None

            def inspector(activity: Activity, description: str):
                nonlocal expected_answer

                assert not description

                if valid_locale == test_locale:
                    expected_answer = activity.text
                else:
                    # Ensure we're actually testing a variation.
                    assert activity.locale != valid_locale

                assert activity.text == expected_answer
                return True

            async def exec_test(turn_context: TurnContext):
                dialog_context = await dialogs.create_context(turn_context)

                results: DialogTurnResult = await dialog_context.continue_dialog()

                if results.status == DialogTurnStatus.Empty:
                    options = PromptOptions(
                        prompt=Activity(
                            type=ActivityTypes.message, text="Please confirm."
                        )
                    )
                    await dialog_context.prompt("prompt", options)
                elif results.status == DialogTurnStatus.Complete:
                    confirmed = results.result
                    if confirmed:
                        await turn_context.send_activity("true")
                    else:
                        await turn_context.send_activity("false")

                await convo_state.save(turn_context)

            async def validator(prompt: PromptValidatorContext) -> bool:
                assert prompt

                if not prompt.recognized.succeeded:
                    await prompt.context.send_activity("Bad input.")

                return prompt.recognized.succeeded

            test_locale = None
            for test_locale in locale_variations:
                convo_state = ConversationState(MemoryStorage())
                dialog_state = convo_state.create_property("dialogState")
                dialogs = DialogSet(dialog_state)

                choice_prompt = ConfirmPrompt("prompt", validator)
                dialogs.add(choice_prompt)

                adapter = DialogTestAdapter(exec_test)

                step1 = await adapter.send(
                    Activity(
                        type=ActivityTypes.message, text="Hello", locale=test_locale
                    )
                )
                await step1.assert_reply(inspector)

        locales = [
            "zh-cn",
            "nl-nl",
            "en-us",
            "fr-fr",
            "de-de",
            "it-it",
            "ja-jp",
            "ko-kr",
            "pt-br",
            "es-es",
            "tr-tr",
            "de-de",
        ]

        locale_tests = []
        for locale in locales:
            locale_tests.append(
                [
                    locale,
                    cap_ending(locale),
                    title_ending(locale),
                    cap_two_letter(locale),
                    lower_two_letter(locale),
                ]
            )

        # Test each valid locale
        for locale_test in locale_tests:
            await exec_test_for_locale(locale_test[0], locale_test)

    @pytest.mark.asyncio
    async def test_should_recognize_and_use_custom_locale_dict(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        culture = PromptCultureModel(
            locale="custom-locale",
            no_in_language="customNo",
            yes_in_language="customYes",
            separator="customSeparator",
            inline_or="customInlineOr",
            inline_or_more="customInlineOrMore",
        )

        custom_dict = {
            culture.locale: (
                Choice(culture.yes_in_language),
                Choice(culture.no_in_language),
                ChoiceFactoryOptions(
                    culture.separator, culture.inline_or, culture.inline_or_more, True
                ),
            )
        }

        confirm_prompt = ConfirmPrompt("prompt", validator, choice_defaults=custom_dict)
        dialogs.add(confirm_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(type=ActivityTypes.message, text="Please confirm.")
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send(
            Activity(type=ActivityTypes.message, text="Hello", locale=culture.locale)
        )
        await step1.assert_reply(
            "Please confirm. (1) customYescustomInlineOr(2) customNo"
        )
