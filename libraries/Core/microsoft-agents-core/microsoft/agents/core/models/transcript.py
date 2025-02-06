from .activity import Activity
from .agents_model import AgentsModel


class Transcript(AgentsModel):
    """Transcript.

    :param activities: A collection of Activities that conforms to the
     Transcript schema.
    :type activities: list[~microsoft.agents.protocols.models.Activity]
    """

    activities: list[Activity] = None
