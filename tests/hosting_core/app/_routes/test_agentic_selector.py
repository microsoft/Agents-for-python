import pytest

from microsoft_agents.activity import Activity, ChannelAccount

from microsoft_agents.hosting.core import RouteSelector, TurnContext
from microsoft_agents.hosting.core.app._routes import _agentic_selector

from tests._common.fixtures.roles import (
    agentic_role,
    non_agentic_role,
)  # required for fixtures


def message_selector(context) -> bool:
    return context.activity.type == "message"


def invoke_selector(context) -> bool:
    return context.activity.type == "invoke"


def create_text_selector(includes: str) -> RouteSelector:
    def text_selector(context) -> bool:
        return context.activity.type == "message" and includes in context.activity.text

    return text_selector


hello_text_selector = create_text_selector("hello")
bye_text_selector = create_text_selector("bye")

do_select = {
    message_selector: Activity(type="message", text="hello world"),
    invoke_selector: Activity(type="invoke"),
    hello_text_selector: Activity(type="message", text="hello there"),
    bye_text_selector: Activity(type="message", text="goodbye"),
}

do_not_select = {
    message_selector: Activity(type="invoke"),
    invoke_selector: Activity(type="message"),
    hello_text_selector: Activity(type="message", text="goodbye"),
    bye_text_selector: Activity(type="message", text="hello there"),
}


@pytest.fixture(
    params=[message_selector, invoke_selector, hello_text_selector, bye_text_selector]
)
def selector(request) -> RouteSelector:
    return request.param


def test_agentic_selector_does_not_select_with_non_agentic_request(
    mocker, selector, non_agentic_role
):
    channel_account = ChannelAccount(role=non_agentic_role)

    selecting_activity = do_select[selector].model_copy()
    non_selecting_activity = do_not_select[selector].model_copy()

    selecting_context = mocker.Mock(spec=TurnContext)
    selecting_context.activity = selecting_activity
    non_selecting_context = mocker.Mock(spec=TurnContext)
    non_selecting_context.activity = non_selecting_activity

    assert selector(selecting_context)
    assert not selector(non_selecting_context)

    new_selector = _agentic_selector(selector)

    selecting_activity.recipient = channel_account

    assert not new_selector(selecting_context)
    assert not new_selector(non_selecting_context)


def test_agentic_selector_selects_with_agentic_request(mocker, selector, agentic_role):
    channel_account = ChannelAccount(role=agentic_role)

    selecting_activity = do_select[selector].model_copy()
    non_selecting_activity = do_not_select[selector].model_copy()

    selecting_context = mocker.Mock(spec=TurnContext)
    selecting_context.activity = selecting_activity
    non_selecting_context = mocker.Mock(spec=TurnContext)
    non_selecting_context.activity = non_selecting_activity

    assert selector(selecting_context)
    assert not selector(non_selecting_context)

    new_selector = _agentic_selector(selector)

    selecting_activity.recipient = channel_account

    assert new_selector(selecting_context)
    assert not new_selector(non_selecting_context)
