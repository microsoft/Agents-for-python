# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import Activity, DeliveryModes

from .core import constants

def format_scopes(scopes: list[str] | None) -> str:
    """Formats a list of scopes into a string for telemetry recording. If the list is None or empty, returns a constant value indicating unknown scopes."""
    if not scopes:
        return constants.UNKNOWN
    return ",".join(scopes)

def get_conversation_id(activity: Activity) -> str:
    """Extracts the conversation ID from the given activity. If the conversation ID cannot be found, returns a constant value indicating unknown conversation ID."""
    return activity.conversation.id if activity.conversation else constants.UNKNOWN


def get_delivery_mode(activity: Activity) -> str:
    """Extracts the delivery mode from the given activity. If the delivery mode cannot be found, returns a constant value indicating unknown delivery mode."""
    if activity.delivery_mode:
        if isinstance(activity.delivery_mode, DeliveryModes):
            return activity.delivery_mode.value
        else:
            return activity.delivery_mode
    return constants.UNKNOWN