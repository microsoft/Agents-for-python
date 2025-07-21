# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .testing_adapter import TestingAdapter
from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    ConversationAccount,
    ChannelAccount,
)
from microsoft.agents.hosting.core import TurnContext


class TestingUtility:
    """Utility methods for testing Microsoft Agents."""

    @staticmethod
    def create_empty_context():
        """
        Creates an empty turn context for testing.

        Returns:
            TurnContext: A turn context with minimal configuration for testing.
        """
        adapter = TestingAdapter()
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
