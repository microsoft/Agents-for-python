# Motivation

## Without this framework

To test an echo agent you need to: get a token, start a callback server,
build the activity JSON, send it, wait, and check the response.

```python
import aiohttp
import asyncio
import json
from aiohttp import web

APP_ID, APP_SECRET, TENANT_ID = "...", "...", "..."

async def get_token() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "scope": f"{APP_ID}/.default",
            },
        ) as resp:
            return (await resp.json())["access_token"]

collected = []

async def _callback_handler(request):
    collected.append(await request.json())
    return web.Response(text="OK")

callback_app = web.Application()
callback_app.router.add_post("/v3/conversations/{path:.*}", _callback_handler)
runner = web.AppRunner(callback_app)

activity = {
    "type": "message",
    "text": "Hello!",
    "channelId": "test",
    "conversation": {"id": "test-conv-123"},
    "from": {"id": "user-1", "name": "Test User"},
    "recipient": {"id": "bot-1", "name": "My Bot"},
    "serviceUrl": "http://localhost:9378/v3/conversations/",
}

async def test_echo():
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 9378)
    await site.start()

    token = await get_token()

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:3978/api/messages",
            json=activity,
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            assert resp.status == 200

    await asyncio.sleep(2)  # hope the callback arrives in time
    await runner.cleanup()

    assert any("Hello" in json.dumps(r) for r in collected)
```

~60 lines to send one message and check for a substring.

---

## With this framework

```python
import pytest
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment

async def init_echo(env: AgentEnvironment):
    @env.agent_application.activity("message")
    async def on_message(context, state):
        await context.send_activity(f"Echo: {context.activity.text}")

scenario = AiohttpScenario(init_agent=init_echo, use_jwt_middleware=False)

@pytest.mark.agent_test(scenario)
class TestEcho:
    async def test_echoes(self, agent_client):
        await agent_client.send("Hello!", wait=0.2)
        agent_client.expect().that_for_any(text="Echo: Hello!")
```

Or without pytest:

```python
...
async with scenario.client() as client:
    await client.send("Hello!", wait=0.2)
    client.expect().that_for_any(text="Echo: Hello!")
```

---

## What moved where

| Before | After |
|---|---|
| `get_token()`, env vars, `Authorization` header | Scenario reads `.env` and handles auth |
| `web.Application()`, `AppRunner`, `TCPSite`, cleanup | Callback server runs inside the scenario |
| Hand-built activity dict | `ActivityTemplate` fills required fields |
| `asyncio.sleep(2)` | `wait=0.2` on `send()` |
| `assert any("Hello" in json.dumps(r) for r in collected)` | `expect().that_for_any(text="Echo: Hello!")` |
| No record of the conversation | `Transcript` captures every exchange |

---

## How it's structured

```
Scenario.run()  →  ClientFactory  →  AgentClient
```

- **Scenario** owns lifecycle (servers, auth, teardown).
- **ClientFactory** creates clients — call it multiple times for multi-user tests.
- **AgentClient** is the API you write tests against.

Swap `AiohttpScenario` for `ExternalScenario` and your assertions stay the same.

The core has no dependency on pytest. The pytest plugin
(`@pytest.mark.agent_test`) is an optional layer that wires scenarios into
fixtures.

---

## Accessing agent internals via fixtures

With external testing you can only observe what an agent *says*.
With `AiohttpScenario` the agent runs **in-process**, so the pytest plugin
exposes its internals as fixtures you can inject into any test:

| Fixture | Type | What it gives you |
|---|---|---|
| `agent_environment` | `AgentEnvironment` | The full environment dataclass (config, app, storage, …) |
| `agent_application` | `AgentApplication` | The running application — register handlers, inspect middleware |
| `authorization` | `Authorization` | Auth handler — swap or inspect auth behaviour |
| `storage` | `Storage` | State storage (default `MemoryStorage`) — read/write agent state directly |
| `adapter` | `ChannelServiceAdapter` | The channel adapter — useful for proactive-message tests |
| `connection_manager` | `Connections` | Connection manager — mock or verify external-service calls |

Because these are plain pytest fixtures, you can combine them freely:

```python
@pytest.mark.agent_test(scenario)
class TestStatePersistence:
    async def test_remembers_name(self, agent_client, storage):
        await agent_client.send("I want to order a cherry soda.", wait=0.3)
        # reach into storage to verify the agent wrote state correctly
        order_store = await storage.read(["drinks"], target_cls=OrderStore)
        assert order_store.size() > 0
        assert "cherry soda" in order_store
```

None of this is possible with raw HTTP tests against a deployed agent — you
would need to add debug endpoints or parse logs after the fact.

---

## Complexity the framework reduces: response collection

Without the framework, collecting responses from an agent is not easy. Agents can send replies within the HTTP response body and through separate POSTs to a service URL, depending on the delivery mode of the activity.

The framework here facilitates response handling by unifying it under the `Transcript` abstraction that is managed by `Scenario`s and `AgentClient`s to automatically record every exchange that takes place with the target agent.

```python
# Framework handles callback server, response routing, and timing
# after sending the request, wait 2 seconds for any incoming activites.
replies = await agent_client.send(activity, wait=2.0)
```

---

## Complexity the framework reduces: assertions

Without the framework, asserting on a list of Activity objects requires
defensive coding: null-guards before accessing nested fields, `or ""`
wrappers to avoid `TypeError` on `None` text, and manual iteration.
When the assertion fails, pytest can only tell you the generator returned
`False` — not which activities were checked or which conditions didn't hold.

Without the framework:

```python
import re

assert any(
    a.type == "message"
    and a.channel_id == "msteams"
    and a.locale == "en-US"
    and "order confirmed" in (a.text or "")          # guard against None
    and re.search(r"Order #\d{6}", a.text or "")     # guard again
    and a.from_property is not None                    # null-check before
    and a.from_property.name == "OrderBot"             #   accessing .name
    and a.conversation is not None                     # null-check before
    and a.conversation.id.startswith("thread-")        #   accessing .id
    for a in replies
)
```

Failure output:

```
E   assert False
E    +  where False = any(<generator object test_raw_assertion.<locals>.<genexpr> at 0x...>)
```

The framework's `Expect` API handles missing/`None` fields automatically
(no crash, just a non-match) and uses dot-notation to reach into nested
objects. When the assertion fails it reports *per item* which fields
didn't match, what was expected, and what was actually there:

With the framework:

```python
import re

agent_client.expect().that_for_any({
    "type": "message",
    "channel_id": "msteams",
    "locale": "en-US",
    "text": lambda x: "order confirmed" in x and re.search(r"Order #\d{6}", x),
    "from.name": "OrderBot",                  # dot-notation — no null-guard needed
    "conversation.id": "~thread-",            # '~' prefix = substring match
})
```

Failure output:

```
E   AssertionError: Expectation failed:
E     ✗ Expected at least one item to match, but none did. 0/2 items matched.
E     Details:
E     Item 0: failed on keys ['channel_id', 'text']
E       channel_id:
 E       expected: 'msteams'
E         actual: 'webchat'
E       text:
E         actual: 'Hello there!'
E     Item 1: failed on keys ['from.name']
E       from.name:
E         expected: 'OrderBot'
E         actual: 'HelperBot'
```
