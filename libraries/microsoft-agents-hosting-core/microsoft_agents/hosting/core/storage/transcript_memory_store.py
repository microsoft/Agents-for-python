# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from threading import Lock
from datetime import datetime, timezone
from typing import List
from .transcript_logger import TranscriptLogger
from .transcript_info import TranscriptInfo
from microsoft_agents.activity import Activity

class TranscriptMemoryStore(TranscriptLogger):
    """
    An in-memory implementation of the TranscriptLogger for storing and retrieving activities.

    This class is thread-safe and stores all activities in a list. It supports logging activities,
    retrieving activities for a specific channel and conversation, and filtering by timestamp.
    Activities with a None timestamp are treated as the earliest possible datetime.
    """
    def __init__(self):
        """
        Initializes the TranscriptMemoryStore.
        """
        self._transcript = []
        self.lock = Lock()
    
    async def log_activity(self, activity: Activity) -> None:
        """
        Asynchronously logs an activity to the in-memory transcript.

        :param activity: The Activity object to log. Must have a valid conversation and conversation id.
        :raises ValueError: If activity, activity.conversation, or activity.conversation.id is None.
        """
        if activity is None:
            raise ValueError("Activity cannot be None")
        if activity.conversation is None:
            raise ValueError("Activity.Conversation cannot be None")
        if activity.conversation.id is None:
            raise ValueError("Activity.Conversation.id cannot be None")
        with self.lock:
            self._transcript.append(activity)

    async def get_transcript_activities(
        self,
        channel_id: str,
        conversation_id: str,
        continuation_token: str = None,
        start_date: datetime = datetime.min.replace(tzinfo=timezone.utc),
    ) -> tuple[list[Activity], str]:
        """
        Retrieves activities for a given channel and conversation, optionally filtered by start_date.

        :param channel_id: The channel ID to filter activities.
        :param conversation_id: The conversation ID to filter activities.
        :param continuation_token: (Unused) Token for pagination.
        :param start_date: Only activities with timestamp >= start_date are returned. None timestamps are treated as datetime.min.
        :return: A tuple containing the filtered list of Activity objects and a continuation token (always None).
        :raises ValueError: If channel_id or conversation_id is None.
        """
        if channel_id is None:
            raise ValueError("channel_id cannot be None")
        if conversation_id is None:
            raise ValueError("conversation_id cannot be None")
        with self.lock:
            # Get the activities that match on channel and conversation id
            relevant_activities = [
                a for a in self._transcript
                if a.channel_id == channel_id and a.conversation and a.conversation.id == conversation_id
            ]
            # sort these by timestamp, treating None as datetime.min
            sorted_relevant_activities = sorted(
                relevant_activities,
                key=lambda a: a.timestamp if a.timestamp is not None else datetime.min.replace(tzinfo=timezone.utc)
            )
            # grab the ones bigger than the requested start date, treating None as datetime.min
            filtered_sorted_activities = [
                a for a in sorted_relevant_activities
                if (a.timestamp if a.timestamp is not None else datetime.min.replace(tzinfo=timezone.utc)) >= start_date
            ]

            return filtered_sorted_activities, None

    async def delete_transcript(self, channel_id: str, conversation_id: str) -> None:

        if channel_id is None:
            raise ValueError("channel_id cannot be None")

        if conversation_id is None:
            raise ValueError("conversation_id cannot be None")
        
        with self.lock:
            self._transcript = [a for a in self._transcript if not (a.channel_id == channel_id and a.conversation and a.conversation.id == conversation_id)]
        
    async def list_transcripts(self, channel_id: str, continuation_token: str = None) -> tuple[list[TranscriptInfo], str]:
        if channel_id is None:
            raise ValueError("channel_id cannot be None")

        with self.lock:
            relevant_activities = [a for a in self._transcript if a.channel_id == channel_id]            
            conversations = set(a.conversation.id for a in relevant_activities if a.conversation and a.conversation.id)            
            transcript_infos = [TranscriptInfo(channel_id=channel_id, conversation_id=conversation_id) for conversation_id in conversations]

            return transcript_infos, None