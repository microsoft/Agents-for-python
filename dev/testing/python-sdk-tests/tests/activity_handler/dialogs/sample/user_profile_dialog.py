# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""UserProfileDialog — multi-step waterfall that collects a user profile.

Steps:
    1. transport_step  — ChoicePrompt: Car / Bus / Bicycle
    2. name_step       — TextPrompt
    3. confirm_age_step — ConfirmPrompt: ask whether to collect age
    4. age_step        — NumberPrompt (validator: 0 < age < 150), or skip with -1
    5. picture_step    — AttachmentPrompt (jpeg/png); plain-text skips gracefully
    6. summary_step    — display summary, ConfirmPrompt: save?
    7. save_step       — persist or discard UserProfile
"""

from microsoft_agents.hosting.core import MessageFactory, UserState
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    DialogTurnResult,
    WaterfallDialog,
    WaterfallStepContext,
)
from microsoft_agents.hosting.dialogs.choices import Choice
from microsoft_agents.hosting.dialogs.prompts import (
    AttachmentPrompt,
    ChoicePrompt,
    ConfirmPrompt,
    NumberPrompt,
    PromptOptions,
    PromptValidatorContext,
    TextPrompt,
)

from .user_profile import UserProfile


class UserProfileDialog(ComponentDialog):
    """ComponentDialog that collects transport, name, age, and a profile picture."""

    def __init__(self, user_state: UserState) -> None:
        super().__init__(UserProfileDialog.__name__)

        self._profile_accessor = user_state.create_property("UserProfile")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self._transport_step,
                    self._name_step,
                    self._confirm_age_step,
                    self._age_step,
                    self._picture_step,
                    self._summary_step,
                    self._save_step,
                ],
            )
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__, self._age_validator)
        )
        self.add_dialog(
            AttachmentPrompt(AttachmentPrompt.__name__, self._picture_validator)
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _transport_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        return await step.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please enter your mode of transport."),
                choices=[Choice("Car"), Choice("Bus"), Choice("Bicycle")],
            ),
        )

    async def _name_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["transport"] = step.result.value
        return await step.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Please enter your name.")),
        )

    async def _confirm_age_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["name"] = step.result
        await step.context.send_activity(
            MessageFactory.text(f"Thanks {step.result}")
        )
        return await step.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Would you like to give your age?")),
        )

    async def _age_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        if step.result:
            return await step.prompt(
                NumberPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please enter your age."),
                    retry_prompt=MessageFactory.text(
                        "The value entered must be greater than 0 and less than 150."
                    ),
                ),
            )
        return await step.next(-1)

    async def _picture_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["age"] = step.result
        msg = (
            "No age given."
            if step.result == -1
            else f"I have your age as {step.result}."
        )
        await step.context.send_activity(MessageFactory.text(msg))

        return await step.prompt(
            AttachmentPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Please attach a profile picture (or type any message to skip)."
                ),
                retry_prompt=MessageFactory.text(
                    "The attachment must be a jpeg/png image file."
                ),
            ),
        )

    async def _summary_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["picture"] = (
            None if not step.result else step.result[0]
        )

        transport = step.values["transport"]
        name = step.values["name"]
        age = step.values["age"]

        summary = f"I have your mode of transport as {transport} and your name as {name}."
        if age != -1:
            summary += f" And age as {age}."
        await step.context.send_activity(MessageFactory.text(summary))

        if step.values["picture"]:
            await step.context.send_activity(
                MessageFactory.attachment(step.values["picture"], "Your profile picture.")
            )
        else:
            await step.context.send_activity("No profile picture provided.")

        return await step.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Is this ok?")),
        )

    async def _save_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        if step.result:
            profile = await self._profile_accessor.get(step.context, UserProfile)
            profile.transport = step.values["transport"]
            profile.name = step.values["name"]
            profile.age = step.values["age"]
            profile.picture = step.values["picture"]
            msg = "Thanks. Your profile was saved successfully."
        else:
            msg = "Thanks. Your profile will not be kept."

        await step.context.send_activity(MessageFactory.text(msg))
        return await step.end_dialog()

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @staticmethod
    async def _age_validator(pc: PromptValidatorContext) -> bool:
        return pc.recognized.succeeded and 0 < pc.recognized.value < 150

    @staticmethod
    async def _picture_validator(pc: PromptValidatorContext) -> bool:
        if not pc.recognized.succeeded:
            await pc.context.send_activity(
                "No attachments received. Proceeding without a profile picture..."
            )
            return True  # allow skipping

        valid = [
            a for a in pc.recognized.value
            if a.content_type in ("image/jpeg", "image/png")
        ]
        pc.recognized.value = valid
        return len(valid) > 0
