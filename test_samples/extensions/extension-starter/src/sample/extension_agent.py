from microsoft_agents.hosting.core import TurnContext, TurnState, RouteRank

from src.extension import (
    ExtensionAgent,
    CustomEventData,
    CustomEventResult,
)

from .app import APP

EXT = ExtensionAgent[TurnState](APP)


@EXT.on_agentic_message_has_hello_event(route_rank=RouteRank.FIRST)
async def message_has_hello_event(
    context: TurnContext, state: TurnState, data: CustomEventData
):
    await context.send_activity(
        f"Hello event detected! User ID: {data.user_id}, Field: {data.field}"
    )


@EXT.on_message_has_hello_event(route_rank=RouteRank.FIRST)
async def message_has_hello_event(
    context: TurnContext, state: TurnState, data: CustomEventData
):
    await context.send_activity(
        f"Hello event detected! User ID: {data.user_id}, Field: {data.field}"
    )

# specifying the event type via the enum
@EXT.on_invoke_custom_event(CustomEventTypes.CUSTOM_EVENT)
async def invoke_custom_event(
    context: TurnContext, state: TurnState, data: CustomEventData
) -> CustomEventResult:
    await context.send_activity(
        f"Custom event triggered {context.activity.type}/{context.activity.name}"
    )
    return CustomEventResult(user_id=data.user_id, field=data.field)

# specifying the event type via a string
@EXT.on_invoke_custom_event("otherCustomEvent")
async def invoke_custom_event(
    context: TurnContext, state: TurnState, data: CustomEventData
) -> CustomEventResult:
    await context.send_activity(
        f"Custom event triggered {context.activity.type}/{context.activity.name}"
    )
    return CustomEventResult(user_id=data.user_id, field=data.field)