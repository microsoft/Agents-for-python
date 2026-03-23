from typing import Mapping, TypeVar

from opentelemetry.util.types import AttributeValue
from microsoft_agents.activity import Activity, DeliveryModes

from . import constants

AttributeMap = Mapping[str, AttributeValue]

def format_scopes(scopes: list[str] | None) -> str:
    if not scopes:
        return constants.UNKNOWN
    return ",".join(scopes)

def get_conversation_id(activity: Activity) -> str:
    return activity.conversation.id if activity.conversation else constants.UNKNOWN


def get_delivery_mode(activity: Activity) -> str:
    if activity.delivery_mode:
        if isinstance(activity.delivery_mode, DeliveryModes):
            return activity.delivery_mode.value
        else:
            return activity.delivery_mode
    return constants.UNKNOWN