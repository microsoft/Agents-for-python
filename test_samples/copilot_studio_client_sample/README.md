# Copilot Studio console client

This sample signs in a user interactively and connects to a published Copilot
Studio agent. With `DIRECT_CONNECT_URL` empty, the client discovers the agent's
conversation endpoints before starting the conversation.

## Setup

Use Python 3.11 or later. From the repository root, create a virtual environment
and install the local SDK and sample dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .\libraries\microsoft-agents-activity -e .\libraries\microsoft-agents-hosting-core -e .\libraries\microsoft-agents-copilotstudio-client --config-settings editable_mode=compat msal msal-extensions
```

Copy `env.TEMPLATE` to `.env` in this directory and fill in the resource IDs:

```dotenv
ENVIRONMENT_ID=<environment-id>
AGENT_IDENTIFIER=<published-agent-schema-name>
TENANT_ID=<tenant-id>
APP_CLIENT_ID=<application-client-id>
TOKEN_CACHE_PATH=
CLOUD=TEST
COPILOT_AGENT_TYPE=PUBLISHED
CUSTOM_POWER_PLATFORM_CLOUD=
DIRECT_CONNECT_URL=
USE_EXPERIMENTAL_ENDPOINT=false
ENABLE_DIAGNOSTICS=false
```

Use `CLOUD=TEST` for an agent in the Test cloud, or `CLOUD=PROD` for production
(the template's default). Cloud enum names are uppercase. The sample derives
the token scope from these settings; Test uses
`https://api.test.powerplatform.com/.default`.

The Entra application must support public-client interactive authentication with
the `http://localhost` redirect URI and the delegated
`CopilotStudio.Copilots.Invoke` permission for the target Power Platform resource,
with consent as required by your tenant. Sign in as a user who can invoke the
published agent. This sample does not use a client secret. An app-only token with
an application role is not equivalent to a delegated user token with that scope.
Changing the cloud or adding an application permission does not grant agent access.

`.env` and the default token cache under `bin` are local, Git-ignored files.
Do not commit secrets or tokens.

## Run

From the repository root with the virtual environment activated:

```powershell
python .\test_samples\copilot_studio_client_sample\app.py
```

Complete the browser sign-in, then enter messages at the `user>` prompt. Use
Ctrl+C to stop. Set `DIRECT_CONNECT_URL` only when you intentionally want to
bypass discovery; prebuilt agents also retain their existing routing.
