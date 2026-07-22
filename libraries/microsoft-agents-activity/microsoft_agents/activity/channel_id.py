# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional, Any

from pydantic_core import CoreSchema, core_schema
from pydantic import GetCoreSchemaHandler

from microsoft_agents.activity.errors import activity_errors


class ChannelId(str):
    """A ChannelId represents a channel and optional sub-channel in the format 'channel:sub_channel'."""

    _channel: str
    _sub_channel: str | None

    def __init__(
        self,
        value: str | None = None,
        *,
        channel: str | None = None,
        sub_channel: str | None = None,
    ) -> None:
        """Accept the public constructor signature after __new__ initializes the instance.

        ChannelId subclasses str, an immutable type, so the string value and derived
        channel parts must be assigned in __new__ when the instance is created.
        """

    def __new__(
        cls,
        value: str | None = None,
        *,
        channel: str | None = None,
        sub_channel: str | None = None,
    ) -> ChannelId:
        """Create a new ChannelId instance.

        :param value: The full channel ID string in the format 'channel:sub_channel'. Must be provided if channel is not provided.
        :param channel: The main channel string. Must be provided if value is not provided. Must not contain ':', as it delimits channels and sub channels.
        :param sub_channel: The sub-channel string.
        :return: A new ChannelId instance.
        :raises ValueError: If the input parameters are invalid. value and channel cannot both be provided.
        """
        if isinstance(value, cls) and channel is None and sub_channel is None:
            return value

        value, channel, sub_channel = cls._normalize(value, channel, sub_channel)

        instance = str.__new__(cls, value)
        instance._channel = channel
        instance._sub_channel = sub_channel
        return instance

    @staticmethod
    def _normalize(
        value: Optional[str],
        channel: Optional[str],
        sub_channel: Optional[str],
    ) -> tuple[str, str, Optional[str]]:
        """Normalize constructor arguments into string, channel, and sub-channel."""
        if isinstance(value, str):
            if channel or sub_channel:
                raise ValueError(str(activity_errors.ChannelIdValueConflict))

            value = value.strip()
            if not value:
                raise TypeError(str(activity_errors.ChannelIdValueMustBeNonEmpty))

            split = value.split(":", 1)
            channel = split[0].strip()
            if not channel:
                raise ValueError(str(activity_errors.ChannelIdValueMustBeNonEmpty))
            sub_channel = (split[1].strip() or None) if len(split) == 2 else None
            return value, channel, sub_channel

        if not isinstance(channel, str) or len(channel.strip()) == 0 or ":" in channel:
            raise TypeError(
                "channel must be a non empty string, and must not contain the ':' character"
            )
        if sub_channel is not None and (not isinstance(sub_channel, str)):
            raise TypeError("sub_channel must be a string if provided")
        channel = channel.strip()
        sub_channel = sub_channel.strip() if sub_channel else None
        if sub_channel:
            return f"{channel}:{sub_channel}", channel, sub_channel
        return channel, channel, None

    @property
    def channel(self) -> str:
        """The main channel, e.g. 'email' in 'email:work'."""
        return self._channel  # type: ignore[return-value]

    @property
    def sub_channel(self) -> str | None:
        """The sub-channel, e.g. 'work' in 'email:work'. May be None."""
        return self._sub_channel

    # https://docs.pydantic.dev/dev/concepts/types/#customizing-validation-with-__get_pydantic_core_schema__
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @staticmethod
    def get_sub_channel(channel_id: str | ChannelId | None) -> str | None:
        """Return the sub-channel from a ChannelId or string."""
        if not channel_id or not channel_id.strip():
            return None
        if isinstance(channel_id, ChannelId):
            return channel_id.sub_channel
        value = channel_id.strip()
        sub = value.split(":", 1)[1].strip() if ":" in value else None
        return sub or None

    @staticmethod
    def get_channel(channel_id: str | ChannelId | None) -> str | None:
        """Return the Bot Framework channel without an optional sub-channel."""
        if not channel_id or not channel_id.strip():
            return channel_id
        if isinstance(channel_id, ChannelId):
            return channel_id.channel
        channel_id = channel_id.strip()
        parsed = channel_id.split(":", 1)[0].strip() if ":" in channel_id else None
        return parsed or channel_id
