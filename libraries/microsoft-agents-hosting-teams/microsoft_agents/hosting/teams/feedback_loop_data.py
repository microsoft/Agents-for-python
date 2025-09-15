from typing import Literal, Union

from microsoft_agents.activity import AgentsModel

class FeedbackLoopActionValue(AgentsModel):
    reaction: Literal["like", "dislike"]
    feedback: Union[str, dict[str, Any]]

class FeedbackLoopData(AgentsModel):
    action_name: Literal["feedback"] = "feedback"
    action_value: FeedbackLoopActionValue
    reply_to_id: str