# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from microsoft_agents.activity import Activity

class TranscriptLogger(ABC):
    @abstractmethod
    async def log_activity(self, activity: Activity) -> None:
        """
        Asynchronously logs an activity.

        :param activity: The activity to log.
        """
        pass