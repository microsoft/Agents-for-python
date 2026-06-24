# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal

from microsoft_teams.api.models import (
    ChannelData,
    FeedbackLoop,
    MeetingInfo,
    NotificationInfo,
    TeamInfo,
)

from microsoft_agents.activity import Activity


def _get_channel_data(activity: Activity) -> ChannelData | None:
    """Get the channel data from the activity, if it exists."""
    if isinstance(activity.channel_data, ChannelData):
        return activity.channel_data
    elif isinstance(activity.channel_data, dict):
        return ChannelData.model_validate(activity.channel_data)
    return None


class TeamsActivity(Activity):
    """A class for working with Teams activities."""

    @staticmethod
    def get_selected_channel_id(self, activity: Activity) -> str | None:
        """Get the ID of the selected channel from the activity, if it exists.

        :param activity: The activity from which to get the selected channel ID.
        :return: The ID of the selected channel, or None if it doesn't exist.
        """
        channel_data = _get_channel_data(activity)
        if (
            channel_data
            and channel_data.settings
            and channel_data.settings.selected_channel
        ):
            return channel_data.settings.selected_channel.id
        return None

    @staticmethod
    def get_channel_id(activity: Activity) -> str | None:
        """Get the ID of the channel from the activity, if it exists.

        :param activity: The activity from which to get the channel ID.
        :return: The ID of the channel, or None if it doesn't exist.
        """
        channel_data = _get_channel_data(activity)
        if channel_data and channel_data.channel:
            return channel_data.channel.id
        return None

    @staticmethod
    def get_meeting_info(activity: Activity) -> MeetingInfo | None:
        """Get the meeting info from the activity, if it exists.

        :param activity: The activity from which to get the meeting info.
        :return: The meeting info, or None if it doesn't exist.
        """
        channel_data = _get_channel_data(activity)
        if channel_data:
            return channel_data.meeting
        return None

    @staticmethod
    def get_team_info(activity: Activity) -> TeamInfo | None:
        """Get the team info from the activity, if it exists."""
        channel_data = _get_channel_data(activity)
        if channel_data:
            return channel_data.team
        return None

    @staticmethod
    def notify_user(
        activity: Activity,
        alert_in_meeting: bool = False,
        external_resource_url: str | None = None,
    ):
        """Notify the user about the activity.

        :param activity: The activity to notify the user about.
        :param alert_in_meeting: Whether to alert the user in a meeting.
        :param external_resource_url: The URL of an external resource to link to.
        """
        channel_data = _get_channel_data(activity)
        if not channel_data:
            channel_data = ChannelData()
            activity.channel_data = channel_data

        channel_data.notification = NotificationInfo(
            alert=not alert_in_meeting,
            alert_in_meeting=alert_in_meeting,
            external_resource_url=external_resource_url,
        )

    @staticmethod
    def enable_feedback_loop(
        activity: Activity, feedback_loop_type: Literal["default", "custom"] = "default"
    ) -> bool:
        """Enable a feedback loop for the activity.

        :param activity: The activity for which to enable the feedback loop.
        :param feedback_loop_type: The type of feedback loop to enable.
        :return: True if the feedback loop was enabled, False otherwise.
        """

        channel_data = _get_channel_data(activity)
        if channel_data is not None:
            return False

        activity.channel_data = ChannelData(
            feedback_loop=FeedbackLoop(type=feedback_loop_type)
        )
        return True
