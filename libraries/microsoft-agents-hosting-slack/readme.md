# Microsoft Agents Hosting - Slack

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/)

Integration library for building Slack agents using the Microsoft 365 Agents SDK. Provides direct-to-Slack responses (the full Slack Web API surface, beyond what Azure Bot Service exposes), a typed `SlackChannelData` envelope with dot-notation property access, and a `SlackStream` helper for `chat.startStream` / `chat.appendStream` / `chat.stopStream`.

## Installation

```bash
pip install microsoft-agents-hosting-slack
```

## Usage

```python
from microsoft_agents.hosting.core.app import AgentApplication
from microsoft_agents.hosting.slack import SlackAgentExtension
from microsoft_agents.hosting.slack.api import SlackChannelData

app = AgentApplication(options)
slack = SlackAgentExtension(app)

@slack.on_message()
async def on_slack_message(context, state):
    channel_data = SlackChannelData.from_activity(context.activity)
    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.get("event.channel"),
            "text": f"You said: {context.activity.text}",
        },
        token=channel_data.api_token,
    )
```

## Key Classes

- **`SlackAgentExtension`** — registers Slack-channel-scoped message/event handlers; exposes `call(...)` and `create_stream(...)`.
- **`SlackChannelData`** — typed wrapper around Bot Service's Slack channel-data payload with `get(path)` / `try_get(path)` accessors.
- **`SlackApi`** — async HTTP client for the Slack Web API.
- **`SlackStream`** — wraps Slack's streaming methods for incremental message updates.
- **`SlackHelpers`** — encode/decode and conversation-id parsing utilities.

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
