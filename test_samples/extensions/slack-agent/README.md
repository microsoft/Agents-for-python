# Slack Agent Sample

Demonstrates the `microsoft-agents-hosting-slack` extension: routing Slack messages and events through an `AgentApplication`, replying via the Slack Web API directly (`chat.postMessage`), posting Block Kit interactive buttons, and using `SlackStream` for incremental message updates.

## Run

From this directory:

```bash
python -m src.main
```

## Behavior

| Slack message | Response |
|---|---|
| `-stream`  | Streams progress chunks + a final feedback-buttons block via `chat.startStream` / `chat.appendStream` / `chat.stopStream`. |
| `-buttons` | Posts a Block Kit message with **Yes** / **No** buttons via `chat.postMessage`. |
| anything else | Echoes `"You said: {text}"` via `chat.postMessage` instead of the usual Bot Service activity reply. |
| any Slack event | Replies `"Agent got: {event name}"`. |
| `conversationUpdate` with members added | Sends "Hello and Welcome!". |

## Configuration

Copy `env.TEMPLATE` to `.env` and fill in the Azure Bot Service service-connection credentials. Slack must be configured as a channel on the Azure Bot Service resource; the `ApiToken` Slack delivers in `channelData` is the token used to authenticate the outbound Slack Web API calls.
