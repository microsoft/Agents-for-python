# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal
from microsoft_agents.activity import AgentsModel, Entity


class QuotedReplyData(AgentsModel):
    """Represents a quoted reply in a Teams activity."""

    message_id: str
    sender_id: str | None = None
    sender_name: str | None = None
    preview: str | None = None
    time: str | None = None
    is_reply_deleted: bool | None = None
    validated_message_reference: bool | None = None


class QuotedReply(Entity):
    """Contains the metadata for a quoted Teams message."""

    type: Literal["quotedReply"] = "quotedReply"
    quoted_reply: QuotedReplyData | None = None
