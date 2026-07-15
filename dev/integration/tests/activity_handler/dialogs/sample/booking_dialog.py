# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""BookingDialog — collects origin, destination, and passenger count for a flight booking.

Steps:
    1. origin_step      — TextPrompt: departure city
    2. destination_step — TextPrompt: arrival city
    3. passengers_step  — NumberPrompt (validator: 1 <= n <= 9) with retry
    4. confirm_step     — ConfirmPrompt: shows summary, asks to confirm
    5. finalize_step    — confirms or cancels the booking
"""

from microsoft_agents.hosting.core import MessageFactory
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    DialogTurnResult,
    WaterfallDialog,
    WaterfallStepContext,
)
from microsoft_agents.hosting.dialogs.prompts import (
    ConfirmPrompt,
    NumberPrompt,
    PromptOptions,
    PromptValidatorContext,
    TextPrompt,
)


class BookingDialog(ComponentDialog):
    """ComponentDialog that collects a simple flight booking."""

    def __init__(self) -> None:
        super().__init__(BookingDialog.__name__)

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self._origin_step,
                    self._destination_step,
                    self._passengers_step,
                    self._confirm_step,
                    self._finalize_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__, self._passengers_validator)
        )
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))

        self.initial_dialog_id = WaterfallDialog.__name__

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _origin_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        return await step.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Where are you flying from?")),
        )

    async def _destination_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["origin"] = step.result
        return await step.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Where are you flying to?")),
        )

    async def _passengers_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["destination"] = step.result
        return await step.prompt(
            NumberPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("How many passengers? (1-9)"),
                retry_prompt=MessageFactory.text(
                    "Please enter a number between 1 and 9."
                ),
            ),
        )

    async def _confirm_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        step.values["passengers"] = int(step.result)
        origin = step.values["origin"]
        dest = step.values["destination"]
        pax = step.values["passengers"]
        summary = f"Route: {origin} → {dest} for {pax} passenger(s). Confirm?"
        return await step.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(summary)),
        )

    async def _finalize_step(self, step: WaterfallStepContext) -> DialogTurnResult:
        if step.result:
            origin = step.values["origin"]
            dest = step.values["destination"]
            pax = step.values["passengers"]
            await step.context.send_activity(
                MessageFactory.text(
                    f"Booking confirmed: {origin} to {dest} for {pax} passenger(s)."
                )
            )
        else:
            await step.context.send_activity(
                MessageFactory.text("Booking cancelled.")
            )
        return await step.end_dialog()

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @staticmethod
    async def _passengers_validator(pc: PromptValidatorContext) -> bool:
        return pc.recognized.succeeded and 1 <= int(pc.recognized.value) <= 9