# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class DeliveryModes(StrEnum):
    normal = "normal"
    notification = "notification"
    expect_replies = "expectReplies"
    ephemeral = "ephemeral"
    stream = "stream"
