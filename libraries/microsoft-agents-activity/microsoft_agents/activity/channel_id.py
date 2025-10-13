# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional, Any

from pydantic_core import CoreSchema, core_schema
from pydantic import GetCoreSchemaHandler


class ChannelId(str):
    """A ChannelId represents a channel and optional sub-channel in the format 'channel:sub_channel'."""

    def __init__(
        self,
        value: Optional[str] = None,
        *,
        channel: Optional[str] = None,
        sub_channel: Optional[str] = None,
    ) -> None:
        """Initialize a ChannelId instance.

        :param value: The full channel ID string in the format 'channel:sub_channel'. Must be provided if channel is not provided.
        :param channel: The main channel string. Must be provided if value is not provided.
        :param sub_channel: The sub-channel string.
        :raises ValueError: If the input parameters are invalid. value and channel cannot both be provided.
        """
        super().__init__()
        if not channel:
            split = self.strip().split(":", 1)
            self._channel = split[0].strip()
            self._sub_channel = split[1].strip() if len(split) == 2 else None
        else:
            self._channel = channel
            self._sub_channel = sub_channel

    def __new__(
        cls,
        value: Optional[str] = None,
        *,
        channel: Optional[str] = None,
        sub_channel: Optional[str] = None,
    ) -> ChannelId:
        """Create a new ChannelId instance.

        :param value: The full channel ID string in the format 'channel:sub_channel'. Must be provided if channel is not provided.
        :param channel: The main channel string. Must be provided if value is not provided. Must not contain ':', as it delimits channels and sub channels.
        :param sub_channel: The sub-channel string.
        :return: A new ChannelId instance.
        :raises ValueError: If the input parameters are invalid. value and channel cannot both be provided.
        """
        if isinstance(value, str):
            if channel or sub_channel:
                raise ValueError(
                    "If value is provided, channel and sub_channel must be None"
                )

            value = value.strip()
            if value:
                return str.__new__(cls, value)
            raise TypeError("value must be a non empty string if provided")
        else:
            if (
                not isinstance(channel, str)
                or len(channel.strip()) == 0
                or ":" in channel
            ):
                raise TypeError(
                    "channel must be a non empty string, and must not contain the ':' character"
                )
            if sub_channel is not None and (not isinstance(sub_channel, str)):
                raise TypeError("sub_channel must be a string if provided")
            channel = channel.strip()
            sub_channel = sub_channel.strip() if sub_channel else None
            if sub_channel:
                return str.__new__(cls, f"{channel}:{sub_channel}")
            return str.__new__(cls, channel)

    @property
    def channel(self) -> str:
        """The main channel, e.g. 'email' in 'email:work'."""
        return self._channel  # type: ignore[return-value]

    @property
    def sub_channel(self) -> Optional[str]:
        """The sub-channel, e.g. 'work' in 'email:work'. May be None."""
        return self._sub_channel

    # https://docs.pydantic.dev/dev/concepts/types/#customizing-validation-with-__get_pydantic_core_schema__
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))
