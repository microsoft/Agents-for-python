from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState
)

from src.extension import ExtensionAgent

APP = AgentApplication()

EXT = ExtensionAgent(APP)

@EXT.on_invoke_custom_event
async def invoke_custom_event(context: TurnContext, state: TurnState, data: CustomEventData):
    await context.send_activity(f"Custom event triggered {context.activity.type}/{context.activity.name}")

@EXT.on_invoke_other_custom_event
async def invoke_other_custom_event(context: TurnContext, state: TurnState):
    await context.send_activity(f"Custom event triggered {context.activity.type}/{context.activity.name}")

@EXT.on_message_reaction_added
async def reaction_added(context: TurnContext, state: TurnState, reaction: str):
    await context.send_activity(f"Reaction added: {reaction}")