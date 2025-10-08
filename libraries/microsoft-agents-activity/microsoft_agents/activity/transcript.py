# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .activity import Activity
from .agents_model import AgentsModel


class Transcript(AgentsModel):
    """Transcript.

    :param activities: A collection of Activities that conforms to the
     Transcript schema.
    :type activities: list[~microsoft_agents.activity.Activity]
    """

    activities: list[Activity] = None
