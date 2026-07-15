# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
from microsoft_agents.activity import Activity


class SubscribeEvent:
    """
    Represents a subscription event containing an activity and optional SSE event ID.
    """

    def __init__(self, activity: Activity, event_id: Optional[str] = None):
        """
        Initialize a SubscribeEvent.

        :param activity: The activity received from the copilot.
        :param event_id: The SSE event ID for resumption (None for JSON responses).
        """
        self.activity = activity
        self.event_id = event_id
