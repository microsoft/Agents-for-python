"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .action_payload import ActionPayload
from .event_envelope import EventEnvelope


class SlackChannelData(BaseModel):
    """
    Data associated with a Slack channel activity, as delivered by Azure Bot
    Service in :attr:`Activity.channel_data`.

    Bot Service historically named the envelope property ``SlackMessage`` and
    the API token ``ApiToken``; this model accepts both the PascalCase JSON
    names (via aliases) and snake_case Python names.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    envelope: Optional[EventEnvelope] = Field(default=None, alias="SlackMessage")
    payload: Optional[ActionPayload] = Field(default=None, alias="Payload")
    api_token: Optional[str] = Field(default=None, alias="ApiToken")

    @property
    def channel(self) -> Optional[str]:
        """Slack channel id, sourced from the envelope or action payload."""
        if self.envelope is not None:
            return self.envelope.get("event.channel")
        if self.payload is not None:
            return self.payload.get("channel")
        return None

    @property
    def thread_ts(self) -> Optional[str]:
        """Thread timestamp, sourced from the envelope event or payload message."""
        if self.envelope is not None:
            return self.envelope.get("event.thread_ts") or self.envelope.get("event.ts")
        if self.payload is not None:
            return self.payload.get("message.thread_ts") or self.payload.get(
                "message.ts"
            )
        return None

    @classmethod
    def from_activity(cls, activity: Any) -> "SlackChannelData":
        """Build a :class:`SlackChannelData` from an Activity's ``channel_data``.

        Accepts ``Activity.channel_data`` that is either a ``dict`` (typical for
        deserialized incoming requests) or already a :class:`SlackChannelData`.
        Returns an empty instance when ``channel_data`` is missing.
        """
        data = getattr(activity, "channel_data", None) if activity is not None else None
        if data is None:
            return cls()
        if isinstance(data, cls):
            return data
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json", by_alias=True)
        return cls.model_validate(data)
