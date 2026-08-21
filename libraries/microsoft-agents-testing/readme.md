# Microsoft Agents Testing

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-testing)](https://pypi.org/project/microsoft-agents-testing/)

Testing utilities for the Microsoft 365 Agents SDK for Python. This package
provides an in-memory channel adapter, fluent conversation assertions, and a
mock user-token client so agent behavior can be tested without a live channel
or token service.

## Features

- **`TestAdapter`** runs activities through the normal middleware and agent
  pipeline while capturing outgoing activities in memory.
- **`TestFlow`** provides fluent helpers for sending activities and asserting
  replies in order.
- **`MockUserTokenClient`** supports stored tokens, magic codes, sign-out, token
  status, and token-exchange scenarios.
- **Async-first** APIs work with the SDK's standard `TurnContext` and
  `ChannelAdapter` abstractions.

## Installation

```bash
pip install microsoft-agents-testing
```

## Quick Start

```python
import pytest

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.testing import TestAdapter, TestFlow


@pytest.mark.asyncio
async def test_echo_agent():
    adapter = TestAdapter()

    async def on_turn(context: TurnContext):
        await context.send_activity(f"Echo: {context.activity.text}")

    await (
        TestFlow(adapter, on_turn)
        .send("hello")
        .assert_reply("Echo: hello")
        .assert_no_more_replies()
        .start_test()
    )
```

## Reply Assertions

Replies can be matched by exact text, partial text, activity properties, or a
custom synchronous or asynchronous validator:

```python
from microsoft_agents.activity import Activity, ActivityTypes


def validate_reply(reply: Activity):
    assert reply.type == ActivityTypes.message
    assert reply.text is not None
    assert reply.text.startswith("Hello")


await (
    TestFlow(adapter, on_turn)
    .send("hi")
    .assert_reply_contains("Hello")
    .send("details")
    .assert_reply(validate_reply)
    .start_test()
)
```

`TestFlow` also supports conversation updates, typing indicators, delays,
mixed activity transcripts, and configurable reply timeouts.

## Testing OAuth Flows

`TestAdapter` uses `MockUserTokenClient` by default. Add a token to test an
already-authenticated user:

```python
adapter = TestAdapter(channel_id="msteams")

adapter.add_user_token(
    connection_name="my-connection",
    channel_id="msteams",
    user_id="user1",
    token="test-token",
)
```

Token exchange can be configured in the same way:

```python
adapter.add_exchangeable_token(
    connection_name="my-connection",
    channel_id="msteams",
    user_id="user1",
    exchangeable_item="exchange-token",
    token="exchanged-token",
)
```

These tokens are stored only in memory and are intended exclusively for tests.

## Scope

The adapter models the turn-processing boundary needed by unit tests. It does
not contact Connector Service, create real proactive conversations, or emulate
channel-specific delivery behavior.

## Related Packages

- [`microsoft-agents-hosting-core`](https://pypi.org/project/microsoft-agents-hosting-core/)
  provides the agent runtime and abstractions used by this package.