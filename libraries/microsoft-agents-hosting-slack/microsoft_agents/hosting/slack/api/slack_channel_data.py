"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any
from typing_extensions import Self

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

    Access this model through ``SlackActivity.slack_channel_data`` or use
    :meth:`from_activity` with a plain turn context's activity. Nested path
    lookups belong to the envelope and payload, not this wrapper. For example,
    when an envelope is present, ``envelope.get("event.channel")`` reads the
    channel and ``envelope.get("event.blocks[0].type")`` reads an array field.
    Unknown Slack fields are preserved.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    envelope: EventEnvelope | None = Field(default=None, alias="SlackMessage")
    payload: ActionPayload | None = Field(default=None, alias="Payload")
    api_token: str | None = Field(default=None, alias="ApiToken")

    @property
    def channel(self) -> str | None:
        """Slack channel id, sourced from the envelope or action payload."""
        obj: Any = None
        if self.envelope is not None:
            obj = self.envelope.get("event.channel")
            if isinstance(obj, dict) and "id" in obj:
                obj = obj.get("id")
        elif self.payload is not None:
            obj = self.payload.get("channel")
            if isinstance(obj, dict) and "id" in obj:
                obj = obj.get("id")
            if not isinstance(obj, str):
                obj = self.payload.get("container.channel_id")
        if isinstance(obj, str):
            return obj
        return None

    @property
    def thread_ts(self) -> str | None:
        """Thread timestamp, sourced from the envelope event or payload message."""
        if self.envelope is not None:
            return self.envelope.get("event.thread_ts", type_=str) or self.envelope.get(
                "event.ts", type_=str
            )
        if self.payload is not None:
            return self.payload.get("message.thread_ts", type_=str) or self.payload.get(
                "message.ts", type_=str
            )
        return None

    @classmethod
    def from_activity(cls, activity: Any) -> Self:
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
