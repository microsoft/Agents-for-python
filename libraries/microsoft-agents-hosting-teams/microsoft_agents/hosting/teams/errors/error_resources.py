# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Teams error resources for Microsoft Agents SDK.

Error codes are in the range -62000 to -62999.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage


class TeamsErrorResources:
    """
    Error messages for Teams operations.

    Error codes are organized in the range -62000 to -62999.
    """

    TeamsBadRequest = ErrorMessage(
        "BadRequest",
        -62000,
    )

    TeamsNotImplemented = ErrorMessage(
        "NotImplemented",
        -62001,
    )

    TeamsContextRequired = ErrorMessage(
        "context is required.",
        -62002,
    )

    TeamsMeetingIdRequired = ErrorMessage(
        "meeting_id is required.",
        -62003,
    )

    TeamsParticipantIdRequired = ErrorMessage(
        "participant_id is required.",
        -62004,
    )

    TeamsTeamIdRequired = ErrorMessage(
        "team_id is required.",
        -62005,
    )

    TeamsTurnContextRequired = ErrorMessage(
        "TurnContext cannot be None",
        -62006,
    )

    TeamsActivityRequired = ErrorMessage(
        "Activity cannot be None",
        -62007,
    )

    TeamsChannelIdRequired = ErrorMessage(
        "The teams_channel_id cannot be None or empty",
        -62008,
    )

    TeamsConversationIdRequired = ErrorMessage(
        "conversation_id is required.",
        -62009,
    )

    def __init__(self):
        """Initialize TeamsErrorResources."""
        pass
