from microsoft.agents.activity import (
    Attachment,
    Channels
)
from microsoft.agents.hosting.core import (
    MessageFactory,
    AgentStatePropertyAccessor,
    TurnContext,
    UserState
)
from microsoft.agents.hosting.dialogs import (
    AttachmentPrompt,
    ChoiceFactory,
    ChoicePrompt,
    ComponentDialog,
    ConfirmPrompt,
    DialogSet,
    DialogTurnStatus,
    NumberPrompt,
    PromptValidatorContext,
    TextPrompt,
    WaterfallDialog,
    WaterfallStepContext
)
from .user_profile import UserProfile

ATTACHMENT_PROMPT = "ATTACHMENT_PROMPT"
CHOICE_PROMPT = "CHOICE_PROMPT"
CONFIRM_PROMPT = "CONFIRM_PROMPT"
NAME_PROMPT = "NAME_PROMPT"
NUMBER_PROMPT = "NUMBER_PROMPT"
USER_PROFILE = "USER_PROFILE"
WATERFALL_DIALOG = "WATERFALL_DIALOG"

class UserProfileDialog(ComponentDialog):

    def __init__(self, user_state: UserState):
        super().__init__("user_profile_dialog")

        self.user_profile = user_state.create_property(USER_PROFILE)
        
        self.add_dialog(TextPrompt(NAME_PROMPT))
        self.add_dialog(ChoicePrompt(CHOICE_PROMPT))
        self.add_dialog(ConfirmPrompt(CONFIRM_PROMPT))
        self.add_dialog(NumberPrompt(NUMBER_PROMPT, self.age_prompt_validator))
        self.add_dialog(AttachmentPrompt(ATTACHMENT_PROMPT, self.picture_prompt_validator))

        self.add_dialog(WaterfallDialog(WATERFALL_DIALOG, [
            # robrandao: todo
        ]))

        self.initial_dialog_id = WATERFALL_DIALOG

    async def run(turnContext: TurnContext, accessor: AgentStatePropertyAccessor):
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)

        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)

    async def _transport_step (step_context: WaterfallStepContext):
        return await step_context.prompt(CHOICE_PROMPT, {
            "choices": ChoiceFactory.to_choices(["Car", "Bus", "Bicycle"]),
            "prompt": "Please enter your mode of transport."
        })
    
    async def _name_step (step_context: WaterfallStepContext):
        step_context.options.transport = step_context.result.value
        return await step_context.prompt(NAME_PROMPT, "What is your name, human?")
    
    async def _name_confirm_step(step_context: WaterfallStepContext):
        step_context.options.name = step_context.result
        await step_context.context.send_activity("Thanks {step_context.result}.")
        return await step_context.prompt(CONFIRM_PROMPT, "Do you want to give your age?", ["yes", "no"])
    
    async def _age_step(step_context: WaterfallStepContext):
        if step_context.result:
            prompt_options = {
                "prompt": "Please enter your age.",
                "retry_prompt": "The value entered must be greater than 0 and less than 150."
            }
            return await step_context.prompt(NUMBER_PROMPT, prompt_options)
        else:
            # robrandao: what?
            return await step_context.next(-1)
    
    async def picture_step(step_context: WaterfallStepContext):
        step_context.options.age = step_context.result
        msg = "No age given." if step_context.options.age == -1 else f"I have your age as {step_context.options.age}."

        await step_context.context.send_activity(msg)

        if step_context.context.activity.channel_id == Channels.Msteams:
            await step_context.context.send_activity("Skipping attachment prompt in Teams channel...")
            return await step_context.next(None) # robrandao : ??
        else:
            prompt_options = {
                "prompt": "Please attach a profile picture (or type any message to skip).",
                "retry_prompt": "The attachment must be a jpeg/png image file."
            }
            return await step_context.prompt(ATTACHMENT_PROMPT, prompt_options)
        
    async def _confirm_step(step_context: WaterfallStepContext):
        msg = "Thanks."
        if step_context.result:
            msg += " Your profile saved successfully."
        else:
            msg += " Your profile was not be kept."

        await step_context.context.send_activity(msg)
        return await step_context.end_dialog()
    
    async def _summary_step(step_context: WaterfallStepContext):
        step_context.options.picture = step_context.result and step_context.result[0]

        user_profile = await self.user_profile.get(step_context.context, UserProfile())
        step_context_options = step_context.options
        user_profile.transport = step_context_options.transport
        user_profile.name = step_context_options.name
        user_profile.age = step_context_options.age
        user_profile.picture = step_context_options.picture

        msg = f"I have your mode of transport as {user_profile.transport} and your name as {user_profile.name}."
        if user_profile.age != -1:
            msg += f" And age as {user_profile.age}."
        msg += "."
        await step_context.context.send_activity(msg)
        if user_profile.picture:
            try:
                await step_context.context.send_activity(
                    MessageFactory.attachment(Attachment(
                        content_type=user_profile.picture.content_type,
                        content_url=user_profile.picture.content_url,
                        name=user_profile.picture.name
                    ))
                )
            except Exception:
                await step_context.context.send_activity(
                    "A profile picture was saved but could not be displayed here."
                )
        return await step_context.prompt(CONFIRM_PROMPT, {"prompt": "Is this okay?"})
    
    async def _age_prompt_validator(prompt_context: PromptValidatorContext):
        value = prompt_context.recognized.value if prompt_context.recognized.succeeded else None
        return value is not None and value > 0 and value < 150
    
    async def picture_prompt_validator(prompt_context: PromptValidatorContext):
        if prompt_context.recognized.succeeded:
            attachments = prompt_context.recognized.value or []
            valid_images = []

            for attachment in attachments:
                if attachment.content_type in ["image/jpeg", "image/png"]:
                    valid_images.append(attachment)

            prompt_context.recognized.value = valid_images

            return len(valid_images) > 0
        else:
            await prompt_context.context.send_activity("No attachments received. Proceeding without a profile picture...")
            return True