from typing import Optional, Any

from pydantic import model_validator, model_serializer

from .agents_model import AgentsModel

class ChannelId(AgentsModel):
    channel: str
    sub_channel: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def split_channel_ids(cls, data: Any) -> Any:
        if isinstance(data, str):
            split = data.strip().split(":", 1)
            return {
                "channel": split[0].strip(),
                "sub_channel": split[1].strip() if len(split) == 2 else None,
            }
        elif isinstance(data, dict):
            return data
        else:
            raise ValueError("Invalid data type for ChannelId")
        
    
    @model_serializer(model="plain")
    def serialize_modeL(self) -> str:
        return self.channel
    
    def is_parent_channel(self, channel_id: str) -> bool:
        return self.channel.lower() == channel_id.lower()

    def is_sub_channel(self) -> bool:
        return bool(self.sub_channel)
    
    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))
    
    def __str__(self) -> str:
        if self.sub_channel:
            return f"{self.channel}:{self.sub_channel}"
        return self.channel