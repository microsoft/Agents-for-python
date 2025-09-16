from typing import Type, Union, Literal, TypeVar, Optional

from microsoft_agents.activity import AgentsModel

from .message_actions_payload_from import MessageActionsPayloadFrom

ReactionType = TypeVar("ReactionType", Literal["like", "heart", "laugh", "surprised", "sad", "angry"])

class MessageActionsPayloadReaction(AgentsModel):
    reaction_type: Optional[ReactionType] = None
    created_date_time: Optional[str] = None
    user: Optional[MessageActionsPayloadFrom] = None

