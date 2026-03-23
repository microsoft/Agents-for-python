from microsoft_agents.activity import Activity, DeliveryModes

from . import core


def _format_scopes(scopes: list[str] | None) -> str:
    if not scopes:
        return core.UNKNOWN
    return ",".join(scopes)

def _get_conversation_id(activity: Activity) -> str:
    return activity.conversation.id if activity.conversation else core.UNKNOWN


def _get_delivery_mode(activity: Activity) -> str:
    if activity.delivery_mode:
        if isinstance(activity.delivery_mode, DeliveryModes):
            return activity.delivery_mode.value
        else:
            return activity.delivery_mode
    return core.UNKNOWN