"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict

from .slack_model import SlackModel


class EventContent(SlackModel):
    """
    The inner ``event`` object from a Slack Events API callback payload.

    Slack calls this the "event content". Because event payloads vary so widely
    by ``type``, every unmodelled field is preserved via Pydantic's
    ``extra="allow"`` and is reachable through :meth:`SlackModel.get` using the
    same snake_case names shown in the Slack docs.

    See https://docs.slack.dev/reference/events
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # ── Common event fields (https://docs.slack.dev/apis/events-api/#event-type-structure)
    type: Optional[str] = None
    event_ts: Optional[str] = None
    user: Optional[str] = None
    ts: Optional[str] = None
    subtype: Optional[str] = None
    channel: Optional[str] = None
    channel_type: Optional[str] = None
    team: Optional[str] = None

    # ── message event fields ──
    text: Optional[str] = None
    client_msg_id: Optional[str] = None

    # ── reaction_added / reaction_removed event fields ──
    reaction: Optional[str] = None
    item_user: Optional[str] = None
