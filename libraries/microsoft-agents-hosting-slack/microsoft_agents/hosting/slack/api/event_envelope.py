"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any

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

    token: str | None = None
    team_id: str | None = None
    context_team_id: str | None = None
    context_enterprise_id: str | None = None
    api_app_id: str | None = None

    # Python name `event_content` ↔ JSON field `event`
    event_content: EventContent | None = Field(default=None, alias="event")

    type: str | None = None
    event_id: str | None = None
    event_time: int | None = None
    authorizations: Any | None = None
    is_ext_shared_channel: bool | None = None
    event_context: str | None = None

    def _normalize_path(self, path: str) -> str:
        """Map the C# property alias ``event_content`` to JSON field ``event``."""
        if path.lower() == "event_content":
            return "event"
        if path.lower().startswith("event_content."):
            return "event" + path[len("event_content") :]
        return path
