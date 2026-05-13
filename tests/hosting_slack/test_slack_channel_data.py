"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Tests for SlackChannelData / EventEnvelope / EventContent deserialization and
path-navigation helpers. JSON fixtures mirror the real Slack Events API
examples from https://docs.slack.dev/apis/events-api/#callback-field
"""

import json

import pytest

from microsoft_agents.hosting.slack.api import (
    EventContent,
    EventEnvelope,
    SlackChannelData,
)

MESSAGE_EVENT_JSON = """
{
  "SlackMessage": {
    "token": "7K85CE7U1wjgFDUHafCiPB7l",
    "team_id": "T0AT0TZM9GD",
    "context_team_id": "T0AT0TZM9GD",
    "context_enterprise_id": null,
    "api_app_id": "A0AT4GSCQHG",
    "event": {
      "type": "message",
      "user": "U0ASNSMMY07",
      "ts": "1776271070.726439",
      "client_msg_id": "c9c2aa5e-03fd-48d6-8665-6680d91c8541",
      "text": "hi",
      "team": "T0AT0TZM9GD",
      "blocks": [
        {
          "type": "rich_text",
          "block_id": "a8bcU",
          "elements": [
            {
              "type": "rich_text_section",
              "elements": [
                { "type": "text", "text": "hi" }
              ]
            }
          ]
        }
      ],
      "channel": "D0AT8AL9LA0",
      "event_ts": "1776271070.726439",
      "channel_type": "im"
    },
    "type": "event_callback",
    "event_id": "Ev0AT2MA48S2",
    "event_time": 1776271070,
    "authorizations": [
      {
        "enterprise_id": null,
        "team_id": "T0AT0TZM9GD",
        "user_id": "U0AT1AL4C5T",
        "is_bot": true,
        "is_enterprise_install": false
      }
    ],
    "is_ext_shared_channel": false,
    "event_context": "4-abc"
  },
  "ApiToken": "xoxb-test-message-token"
}
"""

REACTION_REMOVED_JSON = """
{
  "SlackMessage": {
    "token": "tok",
    "team_id": "T0AT0TZM9GD",
    "api_app_id": "A0AT4GSCQHG",
    "event": {
      "type": "reaction_removed",
      "user": "U0ASNSMMY07",
      "reaction": "raised_hands",
      "item": {
        "type": "message",
        "channel": "D0AT8AL9LA0",
        "ts": "1776373312.421509"
      },
      "item_user": "U0AT1AL4C5T",
      "event_ts": "1776373798.000200"
    },
    "type": "event_callback",
    "event_id": "Ev0AUASNK732",
    "event_time": 1776373798,
    "is_ext_shared_channel": false
  },
  "ApiToken": "xoxb-test-reaction-token"
}
"""


def _channel_data(json_str: str) -> SlackChannelData:
    return SlackChannelData.model_validate(json.loads(json_str))


class TestSlackChannelDataDeserialize:
    def test_envelope_present(self):
        cd = _channel_data(MESSAGE_EVENT_JSON)
        assert cd.envelope is not None

    def test_api_token_preserved(self):
        cd = _channel_data(MESSAGE_EVENT_JSON)
        assert cd.api_token == "xoxb-test-message-token"

    def test_channel_shortcut(self):
        cd = _channel_data(MESSAGE_EVENT_JSON)
        assert cd.channel == "D0AT8AL9LA0"

    def test_thread_ts_falls_back_to_ts(self):
        cd = _channel_data(MESSAGE_EVENT_JSON)
        # event has no thread_ts → fallback to event.ts
        assert cd.thread_ts == "1776271070.726439"

    def test_additional_top_level_field_preserved(self):
        raw = {
            "SlackMessage": {"type": "event_callback", "event": {"type": "message"}},
            "ApiToken": "tok",
            "custom_field": "hello",
        }
        cd = SlackChannelData.model_validate(raw)
        dumped = cd.model_dump(mode="json", by_alias=True)
        assert dumped.get("custom_field") == "hello"


class TestEventEnvelope:
    def test_top_level_fields(self):
        envelope = _channel_data(MESSAGE_EVENT_JSON).envelope
        assert envelope.token == "7K85CE7U1wjgFDUHafCiPB7l"
        assert envelope.team_id == "T0AT0TZM9GD"
        assert envelope.context_enterprise_id is None
        assert envelope.api_app_id == "A0AT4GSCQHG"
        assert envelope.type == "event_callback"
        assert envelope.event_id == "Ev0AT2MA48S2"
        assert envelope.event_time == 1776271070
        assert envelope.is_ext_shared_channel is False

    def test_event_content_present(self):
        envelope = _channel_data(MESSAGE_EVENT_JSON).envelope
        assert envelope.event_content is not None
        assert isinstance(envelope.event_content, EventContent)

    def test_get_authorizations_returns_list(self):
        envelope = _channel_data(MESSAGE_EVENT_JSON).envelope
        auths = envelope.get("authorizations")
        assert isinstance(auths, list)
        assert len(auths) == 1
        assert auths[0]["team_id"] == "T0AT0TZM9GD"
        assert auths[0]["is_bot"] is True

    def test_event_content_alias_prefix_is_supported(self):
        envelope = _channel_data(MESSAGE_EVENT_JSON).envelope
        # `event_content.` should be normalized to `event.`
        assert envelope.get("event_content.channel") == "D0AT8AL9LA0"
        assert envelope.get("event.channel") == "D0AT8AL9LA0"
        assert envelope.get("event_content") == envelope.get("event")


class TestEventContentNamedProperties:
    def test_message_event_named_properties(self):
        content = _channel_data(MESSAGE_EVENT_JSON).envelope.event_content
        assert content.type == "message"
        assert content.user == "U0ASNSMMY07"
        assert content.ts == "1776271070.726439"
        assert content.event_ts == "1776271070.726439"
        assert content.client_msg_id == "c9c2aa5e-03fd-48d6-8665-6680d91c8541"
        assert content.text == "hi"
        assert content.team == "T0AT0TZM9GD"
        assert content.channel == "D0AT8AL9LA0"
        assert content.channel_type == "im"
        assert content.subtype is None
        assert content.reaction is None
        assert content.item_user is None

    def test_reaction_removed_named_properties(self):
        content = _channel_data(REACTION_REMOVED_JSON).envelope.event_content
        assert content.type == "reaction_removed"
        assert content.user == "U0ASNSMMY07"
        assert content.reaction == "raised_hands"
        assert content.item_user == "U0AT1AL4C5T"
        assert content.event_ts == "1776373798.000200"
        assert content.channel is None
        assert content.text is None


class TestEventContentPathNavigation:
    def test_simple_property(self):
        content = _channel_data(MESSAGE_EVENT_JSON).envelope.event_content
        assert content.get("type") == "message"
        assert content.get("text") == "hi"
        assert content.get("channel") == "D0AT8AL9LA0"

    def test_missing_path_returns_default(self):
        content = _channel_data(MESSAGE_EVENT_JSON).envelope.event_content
        assert content.get("nonexistent_field") is None
        assert content.get("nonexistent_field", default="fallback") == "fallback"

    def test_nested_object_path(self):
        content = _channel_data(REACTION_REMOVED_JSON).envelope.event_content
        assert content.get("item.type") == "message"
        assert content.get("item.channel") == "D0AT8AL9LA0"
        assert content.get("item.ts") == "1776373312.421509"

    def test_array_indexing(self):
        content = _channel_data(MESSAGE_EVENT_JSON).envelope.event_content
        assert content.get("blocks[0].type") == "rich_text"
        assert content.get("blocks[0].block_id") == "a8bcU"
        assert content.get("blocks[0].elements[0].type") == "rich_text_section"
        assert content.get("blocks[0].elements[0].elements[0].text") == "hi"

    def test_try_get_found_and_missing(self):
        content = _channel_data(MESSAGE_EVENT_JSON).envelope.event_content
        found, value = content.try_get("text")
        assert found is True and value == "hi"

        found, value = content.try_get("nope")
        assert found is False and value is None


class TestActionPayloadChannelData:
    def test_thread_ts_from_payload_message(self):
        raw = {
            "Payload": {
                "type": "block_actions",
                "channel": {"id": "C123"},
                "message": {"ts": "111.222"},
                "actions": [],
            },
            "ApiToken": "xoxb-x",
        }
        cd = SlackChannelData.model_validate(raw)
        assert cd.payload is not None
        # payload.channel is itself an object in this fixture
        assert cd.channel == {"id": "C123"}
        # path-based access drills into it
        assert cd.payload.get("channel.id") == "C123"
        assert cd.thread_ts == "111.222"


class TestFromActivity:
    def test_from_activity_with_dict_channel_data(self):
        class FakeActivity:
            channel_data = json.loads(MESSAGE_EVENT_JSON)

        cd = SlackChannelData.from_activity(FakeActivity())
        assert cd.api_token == "xoxb-test-message-token"
        assert cd.channel == "D0AT8AL9LA0"

    def test_from_activity_none_channel_data(self):
        class FakeActivity:
            channel_data = None

        cd = SlackChannelData.from_activity(FakeActivity())
        assert cd.envelope is None
        assert cd.api_token is None

    def test_from_activity_passes_through_instance(self):
        existing = SlackChannelData(api_token="abc")

        class FakeActivity:
            channel_data = existing

        cd = SlackChannelData.from_activity(FakeActivity())
        assert cd is existing
