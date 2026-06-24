# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for Teams hosting internal utilities (_utils.py)."""

import re
import pytest
from unittest.mock import AsyncMock, MagicMock

from .helpers import _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_agents.activity import Activity, ActivityTypes
    from microsoft_teams.api.models.channel_data import ChannelData
    from microsoft_agents.hosting.msteams._utils import (
        _get_channel_data,
        _get_channel_event_type,
        _match_selector,
        _send_invoke_response,
    )


class TestMatchSelector:

    def test_none_selector_matches_any_value(self):
        assert _match_selector(None, "anything") is True

    def test_none_selector_matches_none_value(self):
        assert _match_selector(None, None) is True

    def test_string_exact_match(self):
        assert _match_selector("cmd", "cmd") is True

    def test_string_no_match(self):
        assert _match_selector("cmd", "other") is False

    def test_string_does_not_partial_match(self):
        assert _match_selector("cmd", "cmdExtra") is False

    def test_none_value_does_not_match_non_none_selector(self):
        assert _match_selector("cmd", None) is False

    def test_regex_full_match(self):
        assert _match_selector(re.compile(r"cmd\d+"), "cmd42") is True

    def test_regex_no_match(self):
        assert _match_selector(re.compile(r"cmd\d+"), "other") is False

    def test_regex_requires_full_match(self):
        assert _match_selector(re.compile(r"cmd"), "cmdExtra") is False


class TestGetChannelEventType:

    def test_returns_none_when_channel_data_absent(self):
        ctx = _make_context(ActivityTypes.conversation_update)
        assert _get_channel_event_type(ctx) is None

    def test_reads_camel_case_eventType_from_dict(self):
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelCreated"},
        )
        assert _get_channel_event_type(ctx) == "channelCreated"

    def test_reads_snake_case_event_type_from_dict(self):
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"event_type": "channelDeleted"},
        )
        assert _get_channel_event_type(ctx) == "channelDeleted"

    def test_reads_event_type_from_object(self):
        data = MagicMock()
        data.event_type = "teamArchived"
        ctx = _make_context(ActivityTypes.conversation_update)
        ctx.activity.channel_data = data
        assert _get_channel_event_type(ctx) == "teamArchived"

    def test_returns_none_when_object_has_no_event_type(self):
        data = MagicMock(spec=[])
        ctx = _make_context(ActivityTypes.conversation_update)
        ctx.activity.channel_data = data
        assert _get_channel_event_type(ctx) is None


class TestGetChannelData:

    def test_raises_when_channel_data_is_none(self):
        ctx = _make_context(ActivityTypes.conversation_update)
        with pytest.raises(ValueError, match="channel_data"):
            _get_channel_data(ctx.activity)

    def test_returns_existing_channel_data_unchanged(self):
        channel_data = ChannelData()
        ctx = _make_context(ActivityTypes.conversation_update)
        ctx.activity.channel_data = channel_data
        assert _get_channel_data(ctx.activity) is channel_data

    def test_model_validates_from_dict(self):
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "channelCreated"},
        )
        result = _get_channel_data(ctx.activity)
        assert isinstance(result, ChannelData)

    def test_model_validates_camel_case_dict_keys(self):
        ctx = _make_context(
            ActivityTypes.conversation_update,
            channel_data={"eventType": "teamArchived"},
        )
        result = _get_channel_data(ctx.activity)
        assert isinstance(result, ChannelData)


class TestSendInvokeResponse:

    @pytest.mark.asyncio
    async def test_sends_invoke_response_without_body(self):
        ctx = _make_context(ActivityTypes.invoke)
        await _send_invoke_response(ctx)
        ctx.send_activity.assert_awaited_once()
        sent = ctx.send_activity.call_args[0][0]
        assert sent.type == ActivityTypes.invoke_response
        assert sent.value.status == 200
        assert sent.value.body is None

    @pytest.mark.asyncio
    async def test_serializes_pydantic_body(self):
        ctx = _make_context(ActivityTypes.invoke)
        body = Activity(type="message", text="hello")
        await _send_invoke_response(ctx, body)
        sent = ctx.send_activity.call_args[0][0]
        assert sent.value.body == body.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )

    @pytest.mark.asyncio
    async def test_passes_plain_dict_body_through(self):
        ctx = _make_context(ActivityTypes.invoke)
        body = {"key": "value"}
        await _send_invoke_response(ctx, body)
        sent = ctx.send_activity.call_args[0][0]
        assert sent.value.body == {"key": "value"}
