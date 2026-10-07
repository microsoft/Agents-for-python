"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from microsoft_agents.activity import Activity

from .api import SlackChannelData


class SlackActivity(Activity):
    """An :class:`Activity` extended with Slack-specific accessors.

    .. note::
        Instances of this class are produced by reassigning ``__class__`` on an
        existing :class:`Activity` (see :class:`SlackTurnContext`), so no new
        instance fields may be added here -- only methods/properties that derive
        values from the activity's existing ``channel_data``.
    """

    @property
    def slack_channel_data(self) -> SlackChannelData:
        """The typed Slack channel data (envelope / interactive payload) carried
        on this activity's ``channel_data``.

        :return: The parsed :class:`SlackChannelData`, or an empty instance if
            the activity has no Slack channel data.
        """
        return SlackChannelData.from_activity(self)
