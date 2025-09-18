from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState
)

from src.extension import ExtensionAgent

APP = AgentApplication()

EXT = ExtensionAgent(APP)

@EXT.on_custom_event
async def custom_event(context: TurnContext, state: TurnState):
    await context.send_activity(f"Custom event triggered {context.activity.type}/{context.activity.name}")

@EXT.on_message_reaction_added
async def reaction_added(context: TurnContext, state: TurnState, reaction: str):
    await context.send_activity(f"Reaction added: {reaction}")