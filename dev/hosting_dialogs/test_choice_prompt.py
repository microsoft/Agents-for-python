# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List

import pytest
from recognizers_text import Culture

from microsoft_agents.hosting.core import ConversationState, MemoryStorage, TurnContext
from microsoft_agents.hosting.core import CardFactory
from microsoft_agents.hosting.dialogs import (
    DialogSet,
    DialogTurnResult,
    DialogTurnStatus,
    ChoiceRecognizers,
    FindChoicesOptions,
)
from microsoft_agents.hosting.dialogs.choices import (
    Choice,
    ChoiceFactoryOptions,
    ListStyle,
)
from microsoft_agents.hosting.dialogs.prompts import (
    ChoicePrompt,
    PromptCultureModel,
    PromptOptions,
    PromptValidatorContext,
)
from microsoft_agents.activity import Activity, ActivityTypes
from tests.hosting_dialogs.helpers import DialogTestAdapter

_color_choices: List[Choice] = [
    Choice(value="red"),
    Choice(value="green"),
    Choice(value="blue"),
]

_answer_message: Activity = Activity(text="red", type=ActivityTypes.message)
_invalid_message: Activity = Activity(text="purple", type=ActivityTypes.message)


class TestChoicePrompt:
    def test_choice_prompt_with_empty_id_should_fail(self):
        empty_id = ""

        with pytest.raises(TypeError):
            ChoicePrompt(empty_id)

    def test_choice_prompt_with_none_id_should_fail(self):
        none_id = None

        with pytest.raises(TypeError):
            ChoicePrompt(none_id)

    @pytest.mark.asyncio
    async def test_should_call_choice_prompt_using_dc_prompt(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        choice_prompt = ChoicePrompt("ChoicePrompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("ChoicePrompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_call_choice_prompt_with_custom_validator(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt", validator)
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_invalid_message)
        step4 = await step3.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step5 = await step4.send(_answer_message)
        await step5.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_send_custom_retry_prompt(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        choice_prompt = ChoicePrompt("prompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please choose red, blue, or green.",
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_invalid_message)
        step4 = await step3.assert_reply(
            "Please choose red, blue, or green. (1) red, (2) green, or (3) blue"
        )
        step5 = await step4.send(_answer_message)
        await step5.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_send_ignore_retry_prompt_if_validator_replies(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt", validator)
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    retry_prompt=Activity(
                        type=ActivityTypes.message,
                        text="Please choose red, blue, or green.",
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_invalid_message)
        step4 = await step3.assert_reply("Bad input.")
        step5 = await step4.send(_answer_message)
        await step5.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_use_default_locale_when_rendering_choices(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt(
            "prompt", validator, default_locale=Culture.Spanish
        )
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send(Activity(type=ActivityTypes.message, text="Hello"))
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, o (3) blue"
        )
        step3 = await step2.send(_invalid_message)
        step4 = await step3.assert_reply("Bad input.")
        step5 = await step4.send(Activity(type=ActivityTypes.message, text="red"))
        await step5.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_use_context_activity_locale_when_rendering_choices(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt", validator)
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send(
            Activity(type=ActivityTypes.message, text="Hello", locale=Culture.Spanish)
        )
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, o (3) blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_use_context_activity_locale_over_default_locale_when_rendering_choices(
        self,
    ):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt(
            "prompt", validator, default_locale=Culture.Spanish
        )
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send(
            Activity(type=ActivityTypes.message, text="Hello", locale=Culture.English)
        )
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_default_to_english_locale(self):
        async def validator(prompt: PromptValidatorContext) -> bool:
            assert prompt

            if not prompt.recognized.succeeded:
                await prompt.context.send_activity("Bad input.")

            return prompt.recognized.succeeded

        locales = [None, "", "not-supported"]

        for locale in locales:
            convo_state = ConversationState(MemoryStorage())
            dialog_state = convo_state.create_property("dialogState")
            dialogs = DialogSet(dialog_state)

            choice_prompt = ChoicePrompt("prompt", validator)
            dialogs.add(choice_prompt)

            async def exec_test(turn_context: TurnContext):
                dialog_context = await dialogs.create_context(turn_context)

                results: DialogTurnResult = await dialog_context.continue_dialog()

                if results.status == DialogTurnStatus.Empty:
                    options = PromptOptions(
                        prompt=Activity(
                            type=ActivityTypes.message, text="Please choose a color."
                        ),
                        choices=_color_choices,
                    )
                    await dialog_context.prompt("prompt", options)
                elif results.status == DialogTurnStatus.Complete:
                    selected_choice = results.result
                    await turn_context.send_activity(selected_choice.value)

                await convo_state.save(turn_context)

            adapter = DialogTestAdapter(exec_test)

            # Activity.locale uses NonEmptyString which rejects None/""; use model_construct to bypass
            send_activity = Activity.model_construct(
                type=ActivityTypes.message, text="Hello", locale=locale or None
            )
            step1 = await adapter.send(send_activity)
            step2 = await step1.assert_reply(
                "Please choose a color. (1) red, (2) green, or (3) blue"
            )
            step3 = await step2.send(_answer_message)
            await step3.assert_reply("red")

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

                choice_prompt = ChoicePrompt("prompt", validator)
                dialogs.add(choice_prompt)

                async def exec_test(turn_context: TurnContext):
                    dialog_context = await dialogs.create_context(turn_context)

                    results: DialogTurnResult = await dialog_context.continue_dialog()

                    if results.status == DialogTurnStatus.Empty:
                        options = PromptOptions(
                            prompt=Activity(
                                type=ActivityTypes.message,
                                text="Please choose a color.",
                            ),
                            choices=_color_choices,
                        )
                        await dialog_context.prompt("prompt", options)
                    elif results.status == DialogTurnStatus.Complete:
                        selected_choice = results.result
                        await turn_context.send_activity(selected_choice.value)

                    await convo_state.save(turn_context)

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
            culture.locale: ChoiceFactoryOptions(
                inline_or=culture.inline_or,
                inline_or_more=culture.inline_or_more,
                inline_separator=culture.separator,
                include_numbers=True,
            )
        }

        choice_prompt = ChoicePrompt("prompt", validator, choice_defaults=custom_dict)
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
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
            "Please choose a color. (1) redcustomSeparator(2) greencustomInlineOrMore(3) blue"
        )

    @pytest.mark.asyncio
    async def test_should_not_render_choices_if_list_style_none_is_specified(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                    style=ListStyle.none,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply("Please choose a color.")
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_create_prompt_with_inline_choices_when_specified(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        choice_prompt.style = ListStyle.in_line
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_create_prompt_with_list_choices_when_specified(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        choice_prompt.style = ListStyle.list_style
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color.\n\n   1. red\n   2. green\n   3. blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_create_prompt_with_suggested_action_style_when_specified(
        self,
    ):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                    style=ListStyle.suggested_action,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply("Please choose a color.")
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_create_prompt_with_auto_style_when_specified(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                    style=ListStyle.auto,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send(_answer_message)
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_recognize_valid_number_choice(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a color."
                    ),
                    choices=_color_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(
            "Please choose a color. (1) red, (2) green, or (3) blue"
        )
        step3 = await step2.send("1")
        await step3.assert_reply("red")

    @pytest.mark.asyncio
    async def test_should_display_choices_on_hero_card(self):
        size_choices = ["large", "medium", "small"]

        def assert_expected_activity(
            activity: Activity, description
        ):  # pylint: disable=unused-argument
            assert len(activity.attachments) == 1
            assert (
                activity.attachments[0].content_type
                == CardFactory.content_types.hero_card
            )
            assert activity.attachments[0].content.text == "Please choose a size."
            return True

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        # Change the ListStyle of the prompt to ListStyle.hero_card.
        choice_prompt.style = ListStyle.hero_card
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(
                    prompt=Activity(
                        type=ActivityTypes.message, text="Please choose a size."
                    ),
                    choices=size_choices,
                )
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        step2 = await step1.assert_reply(assert_expected_activity)
        step3 = await step2.send("1")
        await step3.assert_reply(size_choices[0])

    @pytest.mark.asyncio
    async def test_should_display_choices_on_hero_card_with_additional_attachment(self):
        size_choices = ["large", "medium", "small"]
        card = CardFactory.adaptive_card(
            {
                "type": "AdaptiveCard",
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.2",
                "body": [],
            }
        )
        card_activity = Activity(type=ActivityTypes.message, attachments=[card])

        def assert_expected_activity(
            activity: Activity, description
        ):  # pylint: disable=unused-argument
            assert len(activity.attachments) == 2
            assert (
                activity.attachments[0].content_type
                == CardFactory.content_types.adaptive_card
            )
            assert (
                activity.attachments[1].content_type
                == CardFactory.content_types.hero_card
            )
            return True

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)

        choice_prompt = ChoicePrompt("prompt")
        # Change the ListStyle of the prompt to ListStyle.hero_card.
        choice_prompt.style = ListStyle.hero_card
        dialogs.add(choice_prompt)

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results: DialogTurnResult = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                options = PromptOptions(prompt=card_activity, choices=size_choices)
                await dialog_context.prompt("prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                selected_choice = results.result
                await turn_context.send_activity(selected_choice.value)

            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)

        step1 = await adapter.send("Hello")
        await step1.assert_reply(assert_expected_activity)

    def test_should_not_find_a_choice_in_an_utterance_by_ordinal(self):
        found = ChoiceRecognizers.recognize_choices(
            "the first one please",
            _color_choices,
            FindChoicesOptions(recognize_numbers=False, recognize_ordinals=False),
        )
        assert not found

    def test_should_not_find_a_choice_in_an_utterance_by_numerical_index(self):
        found = ChoiceRecognizers.recognize_choices(
            "one",
            _color_choices,
            FindChoicesOptions(recognize_numbers=False, recognize_ordinals=False),
        )
        assert not found

    @pytest.mark.asyncio
    async def test_choice_prompt_with_empty_choices_renders_but_errors_on_response(
        self,
    ):
        """ChoicePrompt with an empty choices list renders the prompt without
        error, but raises TypeError when the user responds.

        This is because Find.find_choices() treats an empty list the same as
        None and raises TypeError: "Find: choices cannot be None."  Always
        provide at least one Choice when using ChoicePrompt.
        """
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        dialogs.add(ChoicePrompt("ChoicePrompt"))

        turns = []

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            try:
                results = await dialog_context.continue_dialog()
                if results.status == DialogTurnStatus.Empty:
                    options = PromptOptions(
                        prompt=Activity(type=ActivityTypes.message, text="Choose one:"),
                        choices=[],
                    )
                    await dialog_context.prompt("ChoicePrompt", options)
                    turns.append("prompted")
                else:
                    turns.append("continued")
            except TypeError as exc:
                turns.append(f"error:{exc}")
            await convo_state.save(turn_context)

        adapter = DialogTestAdapter(exec_test)
        # First turn: prompt is sent without error
        await adapter.send("hello")
        assert turns[-1] == "prompted"

        # Second turn: recognition raises because choices is empty
        await adapter.send("red")
        assert turns[-1].startswith("error:")
