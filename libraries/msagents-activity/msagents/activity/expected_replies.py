from .activity import Activity
from .agents_model import AgentsModel


class ExpectedReplies(AgentsModel):
    """ExpectedReplies.

    :param activities: A collection of Activities that conforms to the
     ExpectedReplies schema.
    :type activities: list[~msagents.protocols.models.Activity]
    """

    activities: list[Activity] = None
