# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .test_adapter import TestAdapter
from microsoft.agents.core.models import (
    Activity,
    ActivityTypes,
    ConversationAccount,
    ChannelAccount,
)
from microsoft.agents.builder import TurnContext


class TestUtilities:
    """Utility methods for testing Microsoft Agents."""

    @staticmethod
    def create_empty_context():
        """
        Creates an empty turn context for testing.

        Returns:
            TurnContext: A turn context with minimal configuration for testing.
        """
        adapter = TestAdapter()
        activity = Activity(
            type=ActivityTypes.message,
            channel_id="EmptyContext",
            conversation=ConversationAccount(
                id="test",
            ),
            from_property=ChannelAccount(
                id="empty@empty.context.org",
            ),
        )

        context = TurnContext(adapter, activity)

        return context
