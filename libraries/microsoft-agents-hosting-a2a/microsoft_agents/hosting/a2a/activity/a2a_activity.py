# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-aware :class:`Activity` subclass exposing Teams channel data helpers."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from a2a.types import (
    Part,
    Task,
    TaskState,
    Message
)

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    ChannelAccount,
    RoleTypes,
)

_DEFAULT_USER_ID = "unknown"
_ENTITY_TYPE_TEMPLATE = "application/vnd.microsoft.entity.{0}"

class A2AActivity(Activity):
    """A2A-aware :class:`Activity` subclass exposing A2A protocol data helpers."""

    # @staticmethod
    # def activity_from_message(request_id: str, task_id: str | None, message: Message) -> A2AActivity:

    #     if not task_id and not message.task_id:
    #         raise ValueError("T")
        
    #     task_id = task_id or  message.task_id 

    #     activity = A2AActivity._create_activity(
    #         task_id,
    #         message.parts,
    #         True,
    #         True
    #     )

    # @staticmethod
    # def _create_activity(
    #     conversation_id: str,
    #     parts: list[Part],
    #     is_ingress: bool,
    #     is_streaming: bool
    # ) -> A2AActivity:
    #     """Create an Activity representing an A2A concept."""

    #     agent = ChannelAccount(id="assistant", role=RoleTypes.agent)
    #     user = ChannelAccount(id=_DEFAULT_USER_ID, role=RoleTypes.user)

    #     activity = A2AActivity(
    #         type=ActivityTypes.message,
    #         id=str(uuid4()),
    #         channel_id = Channels.a2a,

    #     )