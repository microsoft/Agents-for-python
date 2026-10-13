# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal
from microsoft_agents.activity import Entity


class TargetedMessageInfo(Entity):
    """Identifies the inbound targeted message associated with a Prompt Preview response."""

    type: Literal["targetedMessageInfo"] = "targetedMessageInfo"
    message_id: str
