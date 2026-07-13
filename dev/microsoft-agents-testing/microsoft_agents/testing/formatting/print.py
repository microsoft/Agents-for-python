# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.testing.core import Transcript

from .activity_transcript_formatter import ActivityTranscriptFormatter
from .conversation_transcript_formatter import ConversationTranscriptFormatter
from .json_transcript_formatter import JsonTranscriptFormatter
    
def print_json(transcript: Transcript) -> None:
    """Print transcript as JSON.

    Convenience function for quick JSON viewing.

    Args:
        transcript: The transcript to print.
    """
    print(JsonTranscriptFormatter()(transcript))

def print_conversation(transcript: Transcript) -> None:
    """Print transcript as a conversation.

    Convenience function for quick conversation viewing.

    Args:
        transcript: The transcript to print.
    """
    print(ConversationTranscriptFormatter()(transcript))

def print_activities(transcript: Transcript) -> None:
    """Print transcript with all activity details.

    Convenience function for debugging.

    Args:
        transcript: The transcript to print.
    """
    print(ActivityTranscriptFormatter()(transcript))