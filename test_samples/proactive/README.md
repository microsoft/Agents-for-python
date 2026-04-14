# Proactive Agent Sample

Demonstrates how`AgentApplication.proactive` enables proactive messaging entirely through the
standard bot messaging endpoint — no separate HTTP trigger endpoint is needed
for in-conversation proactive flows.

## Patterns shown

| Pattern | Command / endpoint | Description |
|---------|--------------------|-------------|
| **Store** | `-s` | Persist the current conversation reference |
| **Sign in** | `-signin` | OAuth sign-in via the "me" connection |
| **Sign out** | `-signout` | OAuth sign-out from the "me" connection |
| **Continue (self)** | `-c` | Proactively continue *this* conversation (requires sign-in) |
| **Continue (stored)** | `-c <id>` | Proactively continue a previously stored conversation |
| **Echo via proactive** | any other message | Echo text back from inside a proactive turn using a custom continuation activity |
| **External notify** | `POST /api/proactive/notify` | Send a one-off notification from outside the bot |

## Prerequisites

- Python 3.10+
- An Azure Bot registration (App ID + Secret)
- An OAuth connection configured in your Azure Bot Service registration
- A tunnel tool such as [dev tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started) or ngrok
- The [M365 Agents Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit) or Teams

## Setup

```bash
cp env.TEMPLATE .env
# Fill in CLIENT_ID, CLIENT_SECRET, TENANT_ID, and the OAuth connection name
```

Install dependencies (from the repo root with the venv active):

```bash
pip install -r test_samples/proactive/requirements.txt
```

Or using editable installs from the repo root:

```bash
. ./scripts/dev_setup.sh
```

## Running

```bash
python test_samples/proactive/proactive_agent.py
```

Listens on `localhost:3978` by default. Set `PORT` in `.env` to override.

## Bot commands

All commands go through the standard `POST /api/messages` endpoint.

| Command | Effect |
|---------|--------|
| `-s` | Store this conversation. Prints the conversation ID. |
| `-signin` | Start the OAuth sign-in flow for the "me" connection. |
| `-signout` | Sign out from the "me" connection. |
| `-c` | Continue *this* conversation proactively (requires sign-in). |
| `-c <id>` | Continue a stored conversation by its ID (requires sign-in). |
| `/help` | Show usage. |
| anything else | Echo via a proactive turn (demonstrates custom continuation activity). |

### Walkthrough

1. Send `-s` → bot replies with the conversation ID.
2. Send `-signin` → complete the OAuth flow.
3. Send `-c` → bot opens a proactive turn on this conversation and reports the token length.
4. Send `-c <id>` → bot opens a proactive turn on the stored conversation and reports the token length.
5. Send `-signout` → clears the "me" token.
6. Send `-c` again → bot replies "Send **-signin** first."
7. Send any text → bot echoes it back through a proactive turn.

## HTTP endpoint

### `POST /api/proactive/notify`

For **external** triggers (schedulers, webhooks). Requires the conversation to
have been stored with `-s` first.

```json
{
  "conversationId": "<id printed by -s>",
  "message": "Hello from outside the bot!"
}
```

```bash
curl -X POST http://localhost:3978/api/proactive/notify \
     -H "Content-Type: application/json" \
     -d '{"conversationId":"<id>","message":"Hello!"}'
```

## How it works

### `-signin` — OAuth sign-in

```python
@AGENT_APP.message("-signin", auth_handlers=["ME"])
async def on_signin(context, state):
    await context.send_activity("Signed in.")
```

The `auth_handlers=["ME"]` parameter causes the SDK to start or resume the
OAuth flow before the handler runs.  By the time the handler is invoked the
user is fully signed in and the token is cached.

### `-signout` — OAuth sign-out

```python
@AGENT_APP.message("-signout")
async def on_signout(context, state):
    await AGENT_APP.auth.sign_out(context, auth_handler_id="me")
    await context.send_activity("Signed out.")
```

### `-c` / `-c <id>` — Continue with sign-in guard

`token_handlers=["ME"]` is passed to `continue_conversation`.  Internally the
SDK calls `_start_or_continue_sign_in` for each listed handler before invoking
the user's handler.  If the user is not signed in and
`ProactiveOptions.fail_on_unsigned_in_connections` is `True` (the default), a
`RuntimeError` is raised — mirroring C#'s `UserNotSignedIn` exception.

```python
try:
    await AGENT_APP.proactive.continue_conversation(
        ADAPTER, conversation_id, _on_continue,
        token_handlers=["ME"],
    )
except RuntimeError:
    await context.send_activity("Send **-signin** first.")
```

Inside `_on_continue` the token is retrieved via:

```python
token_response = await AGENT_APP.auth.get_token(context, auth_handler_id="me")
```

### Echo via proactive — custom `continuation_activity`

```python
conversation = Conversation.from_turn_context(context)
continuation = conversation.conversation_reference.get_continuation_activity()
continuation.value = context.activity   # carry the original message

await AGENT_APP.proactive.continue_conversation(
    ADAPTER, conversation, _on_echo,
    continuation_activity=continuation,
)
```

Inside `_on_echo`, `context.activity.value` holds the original `Activity` so
the handler can read `original.text` without shared state.

## Key classes

| Class | Module |
|-------|--------|
| `Proactive` | `microsoft_agents.hosting.core.app.proactive` |
| `ProactiveOptions` | `microsoft_agents.hosting.core.app.proactive` |
| `Conversation` | `microsoft_agents.hosting.core.app.proactive` |
| `ConversationBuilder` | `microsoft_agents.hosting.core.app.proactive` |
| `ConversationReferenceBuilder` | `microsoft_agents.hosting.core.app.proactive` |
| `CreateConversationOptions` | `microsoft_agents.hosting.core.app.proactive` |
