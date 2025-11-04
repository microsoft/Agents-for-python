# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Activity error resources for Microsoft Agents SDK.

Error codes are in the range -64000 to -64999.
"""

from .error_message import ErrorMessage


class ActivityErrorResources:
    """
    Error messages for activity operations.

    Error codes are organized in the range -64000 to -64999.
    """

    InvalidChannelIdType = ErrorMessage(
        "Invalid type for channel_id: {0}. Expected ChannelId or str.",
        -64000,
        "activity-schema",
    )

    ChannelIdProductInfoConflict = ErrorMessage(
        "Conflict between channel_id.sub_channel and productInfo entity",
        -64001,
        "activity-schema",
    )

    ChannelIdValueConflict = ErrorMessage(
        "If value is provided, channel and sub_channel must be None",
        -64002,
        "activity-schema",
    )

    ChannelIdValueMustBeNonEmpty = ErrorMessage(
        "value must be a non empty string if provided",
        -64003,
        "activity-schema",
    )

    InvalidFromPropertyType = ErrorMessage(
        "Invalid type for from_property: {0}. Expected ChannelAccount or dict.",
        -64004,
        "activity-schema",
    )

    InvalidRecipientType = ErrorMessage(
        "Invalid type for recipient: {0}. Expected ChannelAccount or dict.",
        -64005,
        "activity-schema",
    )

    def __init__(self):
        """Initialize ActivityErrorResources."""
        pass
