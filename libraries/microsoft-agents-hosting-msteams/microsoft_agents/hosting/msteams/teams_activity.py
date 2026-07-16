# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-aware :class:`Activity` subclass exposing Teams channel data helpers."""

from typing import Literal

from microsoft_teams.api.models import (
    ChannelData,
    FeedbackLoop,
    MeetingInfo,
    NotificationInfo,
    TeamInfo,
)

from microsoft_agents.activity import Activity

from ._utils import _try_get_channel_data


class TeamsActivity(Activity):
    """An :class:`Activity` extended with Teams-specific accessors.

    .. note::
        Instances of this class are produced by reassigning ``__class__`` on an
        existing :class:`Activity` (see :class:`TeamsTurnContext`), so no new
        instance fields may be added here -- only methods that derive values
        from the activity's existing ``channel_data``.
    """

    def _get_channel_data(self) -> ChannelData | None:
        """Return the parsed Teams channel data, or None if absent.

        :return: The parsed :class:`ChannelData`, or None if the activity has no
            channel data.
        """
        return _try_get_channel_data(self)

    def get_selected_channel_id(self) -> str | None:
        """Get the ID of the selected channel from the activity, if it exists.

        :return: The ID of the selected channel, or None if it doesn't exist.
        """
        channel_data = self._get_channel_data()
        if (
            channel_data
            and channel_data.settings
            and channel_data.settings.selected_channel
        ):
            return channel_data.settings.selected_channel.id
        return None

    def get_channel_id(self) -> str | None:
        """Get the ID of the channel from the activity, if it exists.

        :return: The ID of the channel, or None if it doesn't exist.
        """
        channel_data = self._get_channel_data()
        if channel_data and channel_data.channel:
            return channel_data.channel.id
        return None

    def get_meeting_info(self) -> MeetingInfo | None:
        """Get the meeting info from the activity, if it exists.

        :return: The meeting info, or None if it doesn't exist.
        """
        channel_data = self._get_channel_data()
        if channel_data:
            return channel_data.meeting
        return None

    def get_team_info(self) -> TeamInfo | None:
        """Get the team info from the activity, if it exists.

        :return: The team info, or None if it doesn't exist.
        """
        channel_data = self._get_channel_data()
        if channel_data:
            return channel_data.team
        return None

    def notify_user(
        self,
        alert_in_meeting: bool = False,
        external_resource_url: str | None = None,
    ):
        """Notify the user about the activity.

        :param alert_in_meeting: Whether to alert the user in a meeting.
        :param external_resource_url: The URL of an external resource to link to.
        """
        channel_data = self._get_channel_data()
        if not channel_data:
            channel_data = ChannelData()

        # in both cases need to re-set it because _get_channel_data() can
        # return a serialized version of the stored data
        self.channel_data = channel_data

        channel_data.notification = NotificationInfo(
            alert=not alert_in_meeting,
            alert_in_meeting=alert_in_meeting,
            external_resource_url=external_resource_url,
        )

    def enable_feedback_loop(
        self, feedback_loop_type: Literal["default", "custom"] = "default"
    ) -> bool:
        """Enable a feedback loop for the activity.

        :param feedback_loop_type: The type of feedback loop to enable.
        :return: True if the feedback loop was enabled, False otherwise.
        """

        channel_data = self._get_channel_data()
        if channel_data is not None:
            return False

        self.channel_data = ChannelData(
            feedback_loop=FeedbackLoop(type=feedback_loop_type)
        )
        return True
