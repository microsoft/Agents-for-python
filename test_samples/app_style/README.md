# App-style samples

This folder contains end-to-end samples that resemble production “app-style” experiences built on the Microsoft 365 Agents Python SDK. The new proactive messaging sample shows how to start a Microsoft Teams conversation or send a proactive message to an existing one.

## Proactive messaging sample

`proactive_messaging_agent.py` hosts two HTTP endpoints:

- `POST /api/createconversation` – creates a new 1:1 Teams conversation with a user and optionally sends an initial message.
- `POST /api/sendmessage` – sends another proactive message to an existing conversation id.

### Prerequisites

1. Python 3.10 or later.
2. Install the Agents Python SDK packages (for example by running `pip install -e libraries/microsoft-agents-*`).
3. A published Copilot Studio agent configured for Teams with application (client) ID, client secret, and tenant ID.

### Configure environment variables

1. Copy `env.TEMPLATE` to `.env` if you have not already.
2. Populate the connection settings used to acquire tokens:
   - `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID`
   - `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET`
   - `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID`
3. Add the proactive messaging settings from the template (bot id, agent id, tenant id, service URL, etc.). Optionally set `PROACTIVEMESSAGING__USERAADOBJECTID` to provide a default recipient.
4. Leave `TOKENVALIDATION__ENABLED=false` for local testing. Set it to `true` and supply a valid bearer token when calling the APIs if you need auth checks.

### Run the sample

```pwsh
python proactive_messaging_agent.py
```

The server listens on `http://localhost:5199` by default. Use the following helper commands to exercise the endpoints (replace the sample values with your own IDs):

```pwsh
# Create a new conversation (returns conversationId)
Invoke-RestMethod -Method POST -Uri "http://localhost:5199/api/createconversation" -ContentType "application/json" -Body (@{ Message = "Hello from proactive sample"; UserAadObjectId = "00000000-0000-0000-0000-000000000123" } | ConvertTo-Json)

# Send another proactive message
Invoke-RestMethod -Method POST -Uri "http://localhost:5199/api/sendmessage" -ContentType "application/json" -Body (@{ ConversationId = "<conversation-id>"; Message = "Second proactive ping" } | ConvertTo-Json)
```

When `TOKENVALIDATION__ENABLED` is `true`, add an `Authorization: Bearer <token>` header to each call. The proactive endpoints will respond with JSON payloads describing success or validation errors.
