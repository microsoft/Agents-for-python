from abc import ABC, abstractmethod
from microsoft_agents.activity.transcript import Activity
from microsoft_agents.hosting.core.storage.transcript_info import TranscriptInfo
from microsoft_agents.hosting.core.storage.transcript_logger import TranscriptLogger

class TranscriptStore(ABC, TranscriptLogger):
    @abstractmethod
    async def LogActivity(self, activity: Activity) -> None:
        """
        Asynchronously logs an activity.

        :param activity: The activity to log.
        """
        pass

    @abstractmethod
    async def GetTranscriptActivities(
        self,
        channel_id: str,
        conversation_id: str,
        continuation_token: str = None,
        start_date: str = None,
    ) -> tuple[list[Activity], str]:
        """
        Asynchronously retrieves activities from a transcript.

        :param channel_id: The channel ID of the conversation.
        :param conversation_id: The conversation ID.
        :param continuation_token: (Optional) A token to continue retrieving activities from a specific point.
        :param start_date: (Optional) The start date to filter activities.
        :return: A tuple containing a list of activities and a continuation token.
        """
        pass

    @abstractmethod
    async def ListTranscripts( self, channel_id: str, continuation_token: str = None) -> tuple[list[TranscriptInfo, str]]:
        """
        Asynchronously lists transcripts for a given channel.

        :param channel_id: The channel ID to list transcripts for.
        :param continuation_token: (Optional) A token to continue listing transcripts from a specific point.
        :return: A tuple containing a list of transcripts and a continuation token.
        """
        pass

    @abstractmethod
    async def DeleteTranscript(self, channel_id: str, conversation_id: str) -> None:
        """
        Asynchronously deletes a transcript.

        :param channel_id: The channel ID of the conversation.
        :param conversation_id: The conversation ID.
        """
        pass    

