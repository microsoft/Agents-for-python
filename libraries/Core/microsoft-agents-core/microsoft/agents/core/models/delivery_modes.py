from enum import Enum


class DeliveryModes(str, Enum):
    normal = "normal"
    notification = "notification"
    expect_replies = "expectReplies"
    ephemeral = "ephemeral"
    stream = "stream"
