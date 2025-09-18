from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState
)

from src.extension import (
    ExtensionAgent,
    CustomEventData,
    CustomEventResult,
)

from src.app import APP
from src.extension import ExtensionAgent

EXT = ExtensionAgent[TurnState](APP)

@EXT.on_invoke_custom_event
async def invoke_custom_event(context: TurnContext, state: TurnState, data: CustomEventData) -> CustomEventResult:
    await context.send_activity(f"Custom event triggered {context.activity.type}/{context.activity.name}")
    return CustomEventResult(
        user_id=data.user_id,
        field=data.field
    )

@EXT.on_invoke_other_custom_event
async def invoke_other_custom_event(context: TurnContext, state: TurnState):
    await context.send_activity(f"Custom event triggered {context.activity.type}/{context.activity.name}")

@EXT.on_message_reaction_added
async def reaction_added(context: TurnContext, state: TurnState, reaction: str):
    await context.send_activity(f"Reaction added: {reaction}")