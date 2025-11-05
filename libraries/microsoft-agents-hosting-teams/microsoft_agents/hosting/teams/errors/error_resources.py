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
        "teams-integration",
    )

    TeamsNotImplemented = ErrorMessage(
        "NotImplemented",
        -62001,
        "teams-integration",
    )

    TeamsContextRequired = ErrorMessage(
        "context is required.",
        -62002,
        "teams-integration",
    )

    TeamsMeetingIdRequired = ErrorMessage(
        "meeting_id is required.",
        -62003,
        "teams-integration",
    )

    TeamsParticipantIdRequired = ErrorMessage(
        "participant_id is required.",
        -62004,
        "teams-integration",
    )

    TeamsTeamIdRequired = ErrorMessage(
        "team_id is required.",
        -62005,
        "teams-integration",
    )

    TeamsTurnContextRequired = ErrorMessage(
        "TurnContext cannot be None",
        -62006,
        "teams-integration",
    )

    TeamsActivityRequired = ErrorMessage(
        "Activity cannot be None",
        -62007,
        "teams-integration",
    )

    TeamsChannelIdRequired = ErrorMessage(
        "The teams_channel_id cannot be None or empty",
        -62008,
        "teams-integration",
    )

    TeamsConversationIdRequired = ErrorMessage(
        "conversation_id is required.",
        -62009,
        "teams-integration",
    )

    def __init__(self):
        """Initialize TeamsErrorResources."""
        pass
