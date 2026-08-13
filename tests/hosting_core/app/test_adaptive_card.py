# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re

import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    AdaptiveCardInvokeResponse,
    ContentTypes,
)
from microsoft_agents.hosting.core import MemoryStorage, TurnContext
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    TurnState,
)
from microsoft_agents.hosting.core.app.adaptive_card import AdaptiveCard
from microsoft_agents.hosting.core.app.adaptive_card.models import (
    AdaptiveCardSearchResult,
)
from microsoft_agents.hosting.core.app.oauth import Authorization
from tests._common.testing_objects import TestingConnectionManager as _ConnectionManager


class _StubAdapter:
    def __init__(self):
        self.sent_activities: list[Activity] = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [None] * len(activities)


def _make_app() -> AgentApplication[TurnState]:
    storage = MemoryStorage()
    return AgentApplication[TurnState](
        options=ApplicationOptions(storage=storage),
        authorization=Authorization(
            storage=storage,
            connection_manager=_ConnectionManager(),
        ),
    )


def _make_context(activity_type: str, **kwargs) -> TurnContext:
    activity = Activity(
        type=activity_type,
        channel_id="test",
        conversation={"id": "conv1"},
        from_property={"id": "user1"},
        recipient={"id": "bot1"},
        service_url="https://test",
        **kwargs,
    )
    return TurnContext(_StubAdapter(), activity)


def _action_execute_value(verb: str, data: dict | None = None) -> dict:
    return {
        "action": {
            "type": "Action.Execute",
            "id": "action-id",
            "verb": verb,
            "data": data or {"testKey": "test-value"},
        },
        "authentication": {},
    }


def _search_value(dataset: str) -> dict:
    return {
        "kind": "search",
        "queryText": "test-query",
        "queryOptions": {"skip": 0, "top": 15},
        "dataset": dataset,
    }


def test_regex_match_searches_value_like_dotnet():
    assert AdaptiveCard._matches(re.compile("save"), "prefix-save-suffix")
    assert not AdaptiveCard._matches(re.compile("^save$"), "prefix-save-suffix")


@pytest.mark.asyncio
async def test_action_execute_exact_verb_matches():
    app = _make_app()
    received_data = None

    @app.adaptive_card.action_execute("test-verb")
    async def handler(context, state, data):
        nonlocal received_data
        received_data = data
        return AdaptiveCardInvokeResponse(
            status_code=200,
            type=ContentTypes.message,
            value="handled",
        )

    context = _make_context(
        ActivityTypes.invoke,
        name="adaptiveCard/action",
        value=_action_execute_value("test-verb"),
    )

    await app._on_activity(context, TurnState())

    assert received_data == {"testKey": "test-value"}
    assert len(context.adapter.sent_activities) == 1
    response = context.adapter.sent_activities[0]
    assert response.type == ActivityTypes.invoke_response
    assert response.value.status == 200
    assert response.value.body == {
        "statusCode": 200,
        "type": ContentTypes.message,
        "value": "handled",
    }


@pytest.mark.asyncio
async def test_action_execute_unmatched_verb_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.action_execute("test-verb")
    async def handler(context, state, data):
        nonlocal called
        called = True
        return AdaptiveCardInvokeResponse(status_code=200)

    context = _make_context(
        ActivityTypes.invoke,
        name="adaptiveCard/action",
        value=_action_execute_value("other-verb"),
    )

    await app._on_activity(context, TurnState())

    assert not called
    assert context.adapter.sent_activities == []


@pytest.mark.asyncio
async def test_action_execute_invalid_value_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.action_execute("test-verb")
    async def handler(context, state, data):
        nonlocal called
        called = True
        return AdaptiveCardInvokeResponse(status_code=200)

    context = _make_context(
        ActivityTypes.invoke,
        name="adaptiveCard/action",
        value="not-an-invoke-value",
    )

    await app._on_activity(context, TurnState())

    assert not called
    assert context.adapter.sent_activities == []


@pytest.mark.asyncio
async def test_action_execute_regex_matches_substring():
    app = _make_app()
    received_data = None

    @app.adaptive_card.action_execute(re.compile("save"))
    async def handler(context, state, data):
        nonlocal received_data
        received_data = data
        return AdaptiveCardInvokeResponse(
            status_code=200,
            type=ContentTypes.message,
            value="saved",
        )

    context = _make_context(
        ActivityTypes.invoke,
        name="adaptiveCard/action",
        value=_action_execute_value("prefix-save-suffix", {"id": 1}),
    )

    await app._on_activity(context, TurnState())

    assert received_data == {"id": 1}
    assert len(context.adapter.sent_activities) == 1
    assert context.adapter.sent_activities[0].type == ActivityTypes.invoke_response


@pytest.mark.asyncio
async def test_action_submit_matches_value_filter():
    app = _make_app()
    received_data = None

    @app.adaptive_card.action_submit("submit")
    async def handler(context, state, data):
        nonlocal received_data
        received_data = data

    context = _make_context(
        ActivityTypes.message,
        value={"verb": "submit", "id": 1},
    )

    await app._on_activity(context, TurnState())

    assert received_data == {"verb": "submit", "id": 1}


@pytest.mark.asyncio
async def test_action_submit_unmatched_verb_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.action_submit("expected")
    async def handler(context, state, data):
        nonlocal called
        called = True

    context = _make_context(
        ActivityTypes.message,
        value={"verb": "other"},
    )

    await app._on_activity(context, TurnState())

    assert not called


@pytest.mark.asyncio
async def test_action_submit_message_with_text_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.action_submit("submit")
    async def handler(context, state, data):
        nonlocal called
        called = True

    context = _make_context(
        ActivityTypes.message,
        text="not an Action.Submit activity",
        value={"verb": "submit"},
    )

    await app._on_activity(context, TurnState())

    assert not called


@pytest.mark.asyncio
async def test_search_exact_dataset_matches():
    app = _make_app()
    received_query = None

    @app.adaptive_card.search("test-dataset")
    async def handler(context, state, query):
        nonlocal received_query
        received_query = query
        return [AdaptiveCardSearchResult(title="Title", value="Value")]

    context = _make_context(
        ActivityTypes.invoke,
        name="application/search",
        value=_search_value("test-dataset"),
    )

    await app._on_activity(context, TurnState())

    assert received_query.parameters.query_text == "test-query"
    assert received_query.parameters.dataset == "test-dataset"
    assert received_query.skip == 0
    assert received_query.count == 15
    assert len(context.adapter.sent_activities) == 1
    response = context.adapter.sent_activities[0]
    assert response.type == ActivityTypes.invoke_response
    assert response.value.status == 200
    assert response.value.body == {
        "statusCode": 200,
        "type": "application/vnd.microsoft.search.searchResponse",
        "value": {"results": [{"title": "Title", "value": "Value"}]},
    }


@pytest.mark.asyncio
async def test_search_unmatched_dataset_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.search("expected-dataset")
    async def handler(context, state, query):
        nonlocal called
        called = True
        return []

    context = _make_context(
        ActivityTypes.invoke,
        name="application/search",
        value=_search_value("other-dataset"),
    )

    await app._on_activity(context, TurnState())

    assert not called
    assert context.adapter.sent_activities == []


@pytest.mark.asyncio
async def test_search_invalid_value_is_ignored():
    app = _make_app()
    called = False

    @app.adaptive_card.search("test-dataset")
    async def handler(context, state, query):
        nonlocal called
        called = True
        return []

    context = _make_context(
        ActivityTypes.invoke,
        name="application/search",
        value={"dataset": "test-dataset"},
    )

    await app._on_activity(context, TurnState())

    assert not called
    assert context.adapter.sent_activities == []


@pytest.mark.asyncio
async def test_search_regex_matches_substring():
    app = _make_app()
    received_query = None

    @app.adaptive_card.search(re.compile("products"))
    async def handler(context, state, query):
        nonlocal received_query
        received_query = query
        return [AdaptiveCardSearchResult(title="Product", value="product-1")]

    context = _make_context(
        ActivityTypes.invoke,
        name="application/search",
        value={
            "kind": "search",
            "queryText": "prod",
            "queryOptions": {"skip": 2, "top": 5},
            "dataset": "contoso-products-v2",
        },
    )

    await app._on_activity(context, TurnState())

    assert received_query.parameters.query_text == "prod"
    assert received_query.parameters.dataset == "contoso-products-v2"
    assert received_query.skip == 2
    assert received_query.count == 5
    assert len(context.adapter.sent_activities) == 1
