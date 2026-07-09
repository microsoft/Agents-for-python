"""Verify the assertion failure outputs shown in MOTIVATION.md.

Run with: pytest tests/test_motivation_assertions.py -v
Both tests are expected to FAIL — the point is to compare the error messages.
"""

import re
from dataclasses import dataclass, field

from microsoft_agents.testing.core.fluent import Expect


# Minimal stand-ins for Activity nested objects
@dataclass
class ChannelAccount:
    id: str = ""
    name: str = ""

@dataclass
class ConversationAccount:
    id: str = ""

@dataclass
class FakeActivity:
    type: str = ""
    channel_id: str = ""
    locale: str = ""
    text: str = ""
    from_property: ChannelAccount | None = None
    conversation: ConversationAccount | None = None


# Two replies that intentionally DON'T fully match the assertion criteria
REPLIES = [
    FakeActivity(
        type="message",
        channel_id="webchat",            # wrong channel
        locale="en-US",
        text="Hello there!",             # wrong text
        from_property=ChannelAccount(id="bot-1", name="OrderBot"),
        conversation=ConversationAccount(id="thread-001"),
    ),
    FakeActivity(
        type="message",
        channel_id="msteams",
        locale="en-US",
        text="Your order confirmed — Order #123456",
        from_property=ChannelAccount(id="bot-2", name="HelperBot"),  # wrong name
        conversation=ConversationAccount(id="thread-002"),
    ),
]


class TestWithoutFramework:
    """Shows what pytest prints for a raw `assert any(...)` failure."""

    def test_raw_assertion(self):
        replies = REPLIES
        assert any(
            a.type == "message"
            and a.channel_id == "msteams"
            and a.locale == "en-US"
            and "order confirmed" in (a.text or "")
            and re.search(r"Order #\d{6}", a.text or "") is not None
            and a.from_property is not None
            and a.from_property.name == "OrderBot"
            and a.conversation is not None
            and a.conversation.id.startswith("thread-")
            for a in replies
        )


class TestWithFramework:
    """Shows what the Expect API prints on failure."""

    def test_expect_assertion(self):
        # Expect works on dicts / BaseModel instances, so convert dataclasses
        reply_dicts = [
            {
                "type": r.type,
                "channel_id": r.channel_id,
                "locale": r.locale,
                "text": r.text,
                "from": {"id": r.from_property.id, "name": r.from_property.name}
                if r.from_property
                else None,
                "conversation": {"id": r.conversation.id}
                if r.conversation
                else None,
            }
            for r in REPLIES
        ]

        Expect(reply_dicts).that_for_any({
            "type": "message",
            "channel_id": "msteams",
            "locale": "en-US",
            "text": lambda x: "order confirmed" in x and re.search(r"Order #\d{6}", x),
            "from.name": "OrderBot",
            "conversation.id": "~thread-",
        })
