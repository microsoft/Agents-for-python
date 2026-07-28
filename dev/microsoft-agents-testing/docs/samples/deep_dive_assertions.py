#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Deep Dive Assertions - fluent assertion engine walkthrough.

Features demonstrated:
  - Expect and Select over plain dictionaries.
  - Exact, substring, dot-notation, dictionary, and root callable criteria.
  - Dictionary criteria flattening and result expansion.
  - Lambda predicates with the x / actual / value convention.
  - Pydantic model support.
  - ActivityExpect, ActivitySelect, ExchangeExpect, and ExchangeSelect.
  - contains for nested values.

Run::

    python -m docs.samples.deep_dive_assertions
"""

from pydantic import BaseModel

from microsoft_agents.activity import Activity, Attachment
from microsoft_agents.testing import (
    ActivityExpect,
    ActivitySelect,
    ExchangeExpect,
    ExchangeSelect,
    Expect,
    Select,
)
from microsoft_agents.testing.core.transport import Exchange
from microsoft_agents.testing.utils import contains

HERO_CARD = "application/vnd.microsoft.card.hero"


class Reply(BaseModel):
    """Small Pydantic model used to show model support."""

    type: str
    text: str
    score: int


def demo_expect() -> None:
    """Assert over plain dictionaries."""
    print("-- Expect --")

    items = [
        {"type": "message", "text": "hello world", "score": 10},
        {"type": "typing", "score": 1},
        {"type": "message", "text": "done", "score": 5},
    ]

    Expect(items).that_for_any(type="message", text="~hello")
    Expect(items).that_for_none(text="~error")
    Expect(items).that_for_exactly(2, type="message")
    Expect(items).is_not_empty().has_count(3)

    print("Expect quantifiers passed.")


def demo_select() -> None:
    """Filter dictionaries before asserting."""
    print("-- Select --")

    items = [
        {"type": "message", "text": "alpha", "score": 1},
        {"type": "message", "text": "bravo", "score": 2},
        {"type": "event", "name": "done", "score": 3},
    ]

    messages = Select(items).where(type="message")
    messages.expect().that_for_any(text="alpha")

    latest_message = messages.last().get()[0]
    assert latest_message["text"] == "bravo"

    non_events = Select(items).where_not(type="event")
    assert non_events.count() == 2

    print("Select filtering and slicing passed.")


def demo_matching_rules() -> None:
    """Show exact, substring, dictionary, dot-notation, and root callable criteria."""
    print("-- Matching rules --")

    activities = [
        {
            "type": "message",
            "text": "welcome back",
            "conversation": {"id": "conversation-1"},
            "from": {"id": "user-1"},
        }
    ]

    Expect(activities).that_for_any(type="message")
    Expect(activities).that_for_any(text="~welcome")
    Expect(activities).that_for_any({"type": "message", "text": "~back"})
    Expect(activities).that_for_any(
        {
            "conversation.id": "conversation-1",
            "from.id": "user-1",
        }
    )
    Expect(activities).that_for_any(lambda x: x["type"] == "message")

    print("All matching forms passed.")


def demo_dictionary_expansion() -> None:
    """Show nested dictionary criteria and dot-notation expansion."""
    print("-- Dictionary handling --")

    activity = {
        "type": "message",
        "conversation": {"id": "conversation-1"},
        "from": {"id": "user-1"},
    }

    nested_criteria = {
        "conversation": {"id": "conversation-1"},
        "from": {"id": "user-1"},
    }
    dot_criteria = {
        "conversation.id": "conversation-1",
        "from.id": "user-1",
    }

    Expect([activity]).that_for_any(nested_criteria)
    Expect([activity]).that_for_any(dot_criteria)

    print("Nested dictionary and dot-notation criteria passed.")


def demo_lambdas() -> None:
    """Show the current lambda invocation convention."""
    print("-- Lambdas --")

    items = [{"text": "Hello from assertions", "score": 42}]

    Expect(items).that_for_any(text=lambda x: x.startswith("Hello"))
    Expect(items).that_for_any(text=lambda actual: "assertions" in actual)
    Expect(items).that_for_any(text=lambda value: value.endswith("assertions"))
    Expect(items).that_for_any(score=lambda x: x > 40)

    print("Lambda predicates passed.")


def demo_pydantic_models() -> None:
    """Assert over Pydantic models."""
    print("-- Pydantic models --")

    replies = [
        Reply(type="message", text="welcome", score=10),
        Reply(type="message", text="done", score=5),
    ]

    Expect(replies).that_for_all(type="message")
    Expect(replies).that_for_any(text="~welcome")
    Expect(replies).that_for_any(lambda x: x.text == "welcome")

    selected = Select(replies).where(score=lambda x: x >= 10).get()
    assert selected[0].text == "welcome"

    print("Pydantic model assertions passed.")


def demo_typed_wrappers() -> None:
    """Use activity and exchange typed wrappers directly."""
    print("-- Typed wrappers --")

    activities = [
        Activity(type="message", text="hello"),
        Activity(type="typing"),
    ]

    ActivityExpect(activities).that_for_any(type="message", text="hello")
    message_activities = ActivitySelect(activities).where(type="message").get()
    assert message_activities[0].text == "hello"

    exchanges = [
        Exchange(
            request=Activity(type="message", text="hello"),
            status_code=200,
            responses=[Activity(type="message", text="reply")],
        )
    ]

    ExchangeExpect(exchanges).that_for_one(status_code=200)
    successful = ExchangeSelect(exchanges).where(status_code=200).get()
    assert successful[0].responses[0].text == "reply"

    print("Typed wrapper assertions passed.")


def demo_contains() -> None:
    """Search nested values inside activity payloads."""
    print("-- contains --")

    activities = [
        Activity(
            type="message",
            text="card reply",
            attachments=[
                Attachment(
                    content_type=HERO_CARD,
                    content={"title": "Deep dive"},
                )
            ],
        )
    ]

    Expect(activities).that_for_any(attachments=contains(content_type=HERO_CARD))
    ActivitySelect(activities).where(
        contains(content_type=HERO_CARD)
    ).expect().is_not_empty()

    print("Nested contains assertions passed.")


def main() -> None:
    print("Deep Dive Assertions Demo\n")

    demo_expect()
    demo_select()
    demo_matching_rules()
    demo_dictionary_expansion()
    demo_lambdas()
    demo_pydantic_models()
    demo_typed_wrappers()
    demo_contains()

    print("\nAll assertion demos complete.")


if __name__ == "__main__":
    main()
