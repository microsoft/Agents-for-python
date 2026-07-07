"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict, Field

from .event_content import EventContent
from .slack_model import SlackModel


class EventEnvelope(SlackModel):
    """
    Outer envelope for a Slack Events API callback. Contains workspace, application,
    and authorization context, plus the inner event payload (``event_content``).

    See https://docs.slack.dev/apis/events-api/#callback-field.

    Path navigation supports both the Slack JSON prefix ``event.`` and the Python
    property prefix ``event_content.`` interchangeably::

        envelope = SlackChannelData.from_activity(turn_context.activity).envelope
        workspace_id = envelope.get("team_id")
        channel      = envelope.get("event.channel")
        block_type   = envelope.get("event.blocks[0].type")
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    token: Optional[str] = None
    team_id: Optional[str] = None
    context_team_id: Optional[str] = None
    context_enterprise_id: Optional[str] = None
    api_app_id: Optional[str] = None

    # Python name `event_content` ↔ JSON field `event`
    event_content: Optional[EventContent] = Field(default=None, alias="event")

    type: Optional[str] = None
    event_id: Optional[str] = None
    event_time: Optional[int] = None
    authorizations: Optional[Any] = None
    is_ext_shared_channel: Optional[bool] = None
    event_context: Optional[str] = None

    def _normalize_path(self, path: str) -> str:
        """Map the C# property alias ``event_content`` to JSON field ``event``."""
        if path.lower() == "event_content":
            return "event"
        if path.lower().startswith("event_content."):
            return "event" + path[len("event_content") :]
        return path
