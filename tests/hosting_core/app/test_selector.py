"""Tests for AgentApplication route selector helpers."""

import re
from types import SimpleNamespace

from microsoft_agents.activity import Activity, ActivityTypes, ChannelId
from microsoft_agents.hosting.core.app._selector import (
    _SimpleRouteSelector,
    _activity_type_selector,
    _all_selector,
    _channel_selector,
    _invoke_event_selector,
    _text_selector,
)


def _context(**activity_values):
    activity_values.setdefault("type", ActivityTypes.message)
    return SimpleNamespace(activity=Activity(**activity_values))


def test_text_selector_matches_exact_text():
    selector = _text_selector("hello")

    assert selector(_context(text="hello"))
    assert not selector(_context(text="hello world"))
    assert not selector(_context())


def test_text_selector_uses_regex_fullmatch():
    selector = _text_selector(re.compile(r"hello.*"))

    assert selector(_context(text="hello world"))
    assert not selector(_context(text="well, hello"))


def test_text_selector_matches_any_value_in_mixed_list():
    selector = _text_selector(["hello", re.compile(r"goodbye.*")])

    assert selector(_context(text="hello"))
    assert selector(_context(text="goodbye everyone"))
    assert not selector(_context(text="good morning"))


def test_text_selector_treats_missing_text_as_empty_string():
    assert _text_selector("")(_context())
    assert not _text_selector("hello")(_context())


def test_invoke_event_selector_requires_matching_invoke_name():
    selector = _invoke_event_selector("handoff/action")

    assert selector(_context(type=ActivityTypes.invoke, name="handoff/action"))
    assert not selector(_context(type=ActivityTypes.invoke, name="other/action"))
    assert not selector(_context(type=ActivityTypes.message, name="handoff/action"))
    assert not selector(_context(type=ActivityTypes.invoke))


def test_activity_type_selector_matches_single_type_or_list():
    assert _activity_type_selector("event")(_context(type="event"))
    assert not _activity_type_selector("event")(_context(type="message"))

    selector = _activity_type_selector(["event", ActivityTypes.message])
    assert selector(_context(type="event"))
    assert selector(_context(type=ActivityTypes.message))
    assert not selector(_context(type=ActivityTypes.invoke))


def test_channel_selector_without_filter_matches_any_channel():
    selector = _channel_selector(None)

    assert selector(_context(channel_id="msteams"))
    assert selector(_context())


def test_parent_channel_selector_matches_any_subchannel_of_parent():
    selector = _channel_selector("msteams")

    assert selector(_context(channel_id="msteams:copilot"))
    assert selector(_context(channel_id="msteams:meeting"))
    assert not selector(_context(channel_id="webchat"))
    assert not selector(_context())


def test_subchannel_selector_requires_exact_subchannel():
    selector = _channel_selector(ChannelId("msteams:copilot"))

    assert selector(_context(channel_id="msteams:copilot"))
    assert not selector(_context(channel_id="msteams:meeting"))
    assert not selector(_context(channel_id="msteams"))


def test_all_selector_requires_every_selector_to_match():
    selector = _all_selector(
        _activity_type_selector(ActivityTypes.message),
        _channel_selector("msteams"),
        _text_selector("hello"),
    )

    assert selector(
        _context(
            type=ActivityTypes.message,
            channel_id="msteams:copilot",
            text="hello",
        )
    )
    assert not selector(
        _context(type=ActivityTypes.message, channel_id="webchat", text="hello")
    )


def test_simple_route_selector_combines_channel_type_and_text():
    selector = _SimpleRouteSelector(
        channel_id="msteams",
        activity_type=[ActivityTypes.message, ActivityTypes.event],
        text_pattern=["hello", re.compile(r"goodbye.*")],
    )

    assert selector(
        _context(
            type=ActivityTypes.message,
            channel_id="msteams:copilot",
            text="hello",
        )
    )
    assert selector(
        _context(
            type=ActivityTypes.event,
            channel_id="msteams",
            text="goodbye everyone",
        )
    )
    assert not selector(
        _context(
            type=ActivityTypes.invoke,
            channel_id="msteams",
            text="hello",
        )
    )
    assert not selector(
        _context(
            type=ActivityTypes.message,
            channel_id="webchat",
            text="hello",
        )
    )
    assert not selector(
        _context(
            type=ActivityTypes.message,
            channel_id="msteams",
            text="unmatched",
        )
    )
