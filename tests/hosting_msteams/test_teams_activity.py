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
    from microsoft_agents.activity import ActivityTypes, ChannelAccount
    from microsoft_teams.api.models import (
        ChannelData,
        ChannelInfo,
        FeedbackLoop,
        MeetingInfo,
        TeamInfo,
    )
    from microsoft_teams.api.models.channel_data.settings import ChannelDataSettings

    from microsoft_agents.hosting.msteams import TeamsActivity
    from microsoft_agents.hosting.msteams.models import QuotedReplyData


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


class TestPromptPreview:

    def test_is_recipient_targeted_reads_wire_property(self):
        recipient = ChannelAccount.model_validate({"id": "user-id", "isTargeted": True})
        activity = TeamsActivity(
            type=ActivityTypes.message,
            recipient=recipient,
        )

        assert activity.is_recipient_targeted() is True

    def test_add_quoted_reply_adds_escaped_self_closing_placeholder(self):
        activity = TeamsActivity(type=ActivityTypes.message, text="")

        activity.add_quoted_reply('message&"id', "response")

        quoted_reply = activity.get_quoted_messages()[0]
        assert quoted_reply.quoted_reply.message_id == 'message&"id'
        assert activity.text == '<quoted messageId="message&amp;&quot;id"/> response'

    def test_add_quoted_reply_without_existing_or_appended_text(self):
        activity = TeamsActivity(type=ActivityTypes.message)

        activity.add_quoted_reply("message-id")

        assert activity.text == '<quoted messageId="message-id"/>'

    def test_quoted_reply_validated_reference_round_trips_wire_name(self):
        data = QuotedReplyData.model_validate(
            {
                "messageId": "message-id",
                "validatedMessageReference": True,
            }
        )

        assert data.validated_message_reference is True
        assert data.model_dump(by_alias=True, exclude_none=True) == {
            "messageId": "message-id",
            "validatedMessageReference": True,
        }
