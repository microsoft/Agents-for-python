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
