# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the TeamsActivity helper methods.

These tests operate on real ``TeamsActivity`` / ``ChannelData`` objects rather
than mocks, so they exercise the actual parsing and mutation logic.
"""

import pytest

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api.models import (
        ChannelData,
        ChannelInfo,
        FeedbackLoop,
        MeetingInfo,
        TeamInfo,
    )
    from microsoft_teams.api.models.channel_data.settings import ChannelDataSettings

    from microsoft_agents.hosting.msteams import TeamsActivity


def _activity(channel_data=None) -> "TeamsActivity":
    return TeamsActivity(type="message", channel_data=channel_data)


class TestGetChannelData:

    def test_returns_none_when_channel_data_absent(self):
        assert _activity()._get_channel_data() is None

    def test_returns_channel_data_instance_unchanged(self):
        cd = ChannelData(channel=ChannelInfo(id="c1"))
        assert _activity(cd)._get_channel_data() is cd

    def test_model_validates_dict_channel_data(self):
        result = _activity({"channel": {"id": "c1"}})._get_channel_data()
        assert isinstance(result, ChannelData)
        assert result.channel.id == "c1"


class TestGetSelectedChannelId:

    def test_returns_selected_channel_id(self):
        cd = ChannelData(
            settings=ChannelDataSettings(selected_channel=ChannelInfo(id="sel-1"))
        )
        assert _activity(cd).get_selected_channel_id() == "sel-1"

    def test_returns_none_when_no_channel_data(self):
        assert _activity().get_selected_channel_id() is None

    def test_returns_none_when_settings_absent(self):
        cd = ChannelData(channel=ChannelInfo(id="c1"))
        assert _activity(cd).get_selected_channel_id() is None


class TestGetChannelId:

    def test_returns_channel_id(self):
        cd = ChannelData(channel=ChannelInfo(id="c1"))
        assert _activity(cd).get_channel_id() == "c1"

    def test_returns_none_when_no_channel_data(self):
        assert _activity().get_channel_id() is None

    def test_returns_none_when_channel_absent(self):
        cd = ChannelData(team=TeamInfo(id="t1"))
        assert _activity(cd).get_channel_id() is None


class TestGetMeetingInfo:

    def test_returns_meeting(self):
        meeting = MeetingInfo(id="m1")
        cd = ChannelData(meeting=meeting)
        assert _activity(cd).get_meeting_info() is meeting

    def test_returns_none_when_no_channel_data(self):
        assert _activity().get_meeting_info() is None

    def test_returns_none_when_meeting_absent(self):
        cd = ChannelData(channel=ChannelInfo(id="c1"))
        assert _activity(cd).get_meeting_info() is None


class TestGetTeamInfo:

    def test_returns_team(self):
        team = TeamInfo(id="t1")
        cd = ChannelData(team=team)
        assert _activity(cd).get_team_info() is team

    def test_returns_none_when_no_channel_data(self):
        assert _activity().get_team_info() is None

    def test_returns_none_when_team_absent(self):
        cd = ChannelData(channel=ChannelInfo(id="c1"))
        assert _activity(cd).get_team_info() is None


class TestNotifyUser:

    def test_creates_channel_data_when_absent(self):
        activity = _activity()
        activity.notify_user()
        assert isinstance(activity.channel_data, ChannelData)
        assert activity.channel_data.notification is not None

    def test_alert_true_when_not_in_meeting(self):
        activity = _activity()
        activity.notify_user(alert_in_meeting=False)
        notification = activity.channel_data.notification
        assert notification.alert is True
        assert notification.alert_in_meeting is False

    def test_alert_false_when_in_meeting(self):
        activity = _activity()
        activity.notify_user(alert_in_meeting=True)
        notification = activity.channel_data.notification
        assert notification.alert is False
        assert notification.alert_in_meeting is True

    def test_external_resource_url_is_propagated(self):
        activity = _activity()
        activity.notify_user(external_resource_url="https://example.com/card")
        assert (
            activity.channel_data.notification.external_resource_url
            == "https://example.com/card"
        )

    def test_persists_notification_when_channel_data_is_dict(self):
        # _try_get_channel_data returns a NEW ChannelData parsed from the dict;
        # the notification must be written back so it is not lost.
        activity = _activity({"channel": {"id": "c1"}})
        activity.notify_user(alert_in_meeting=True)
        assert isinstance(activity.channel_data, ChannelData)
        assert activity.channel_data.notification.alert_in_meeting is True
        # existing channel data is preserved
        assert activity.channel_data.channel.id == "c1"


class TestEnableFeedbackLoop:

    def test_enables_when_no_channel_data(self):
        activity = _activity()
        assert activity.enable_feedback_loop() is True
        assert isinstance(activity.channel_data.feedback_loop, FeedbackLoop)
        assert activity.channel_data.feedback_loop.type == "default"

    def test_uses_supplied_feedback_loop_type(self):
        activity = _activity()
        assert activity.enable_feedback_loop("custom") is True
        assert activity.channel_data.feedback_loop.type == "custom"

    @pytest.mark.xfail(
        reason="BUGS.md #1: enable_feedback_loop guard is inverted; it returns "
        "False (no-op) when channel data already exists, which is the common case.",
        strict=True,
    )
    def test_enables_when_channel_data_already_present(self):
        activity = _activity({"channel": {"id": "c1"}})
        assert activity.enable_feedback_loop() is True
        assert activity.channel_data.feedback_loop is not None
        # existing channel data should be preserved, not clobbered
        assert activity.channel_data.channel.id == "c1"
