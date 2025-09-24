from abc import ABC, abstractmethod
from microsoft_agents.activity.transcript import Activity

class TranscriptLogger(ABC):
    @abstractmethod
    async def LogActivity(self, activity: Activity) -> None:
        """
        Asynchronously logs an activity.

        :param activity: The activity to log.
        """
        pass