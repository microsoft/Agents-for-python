from __future__ import annotations

from typing import Optional, Any

from pydantic import model_validator, model_serializer

from ._type_aliases import NonEmptyString
from .agents_model import AgentsModel


class ChannelId(AgentsModel):
    """A class representing a channel identifier with optional sub-channel.

    :param channel: The main channel identifier (e.g., "msteams").
    :type channel: str
    :param sub_channel: An optional sub-channel identifier (e.g., "subchannel").
    :type sub_channel: Optional[str]
    """

    channel: NonEmptyString
    sub_channel: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _split_channel_ids(cls, data: Any) -> Any:
        """Validator to split a string into channel and sub_channel if needed."""
        if isinstance(data, str) and data:
            split = data.strip().split(":", 1)
            return {
                "channel": split[0].strip(),
                "sub_channel": split[1].strip() if len(split) == 2 else None,
            }
        elif isinstance(data, dict) and data:
            return data
        else:
            raise ValueError("Invalid data type for ChannelId")

    @model_serializer(mode="plain")
    def _serialize_plain(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        if self.sub_channel:
            return f"{self.channel}:{self.sub_channel}"
        return self.channel
