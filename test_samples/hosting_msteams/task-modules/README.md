# Teams Task Modules Sample

Python port of the .NET `TaskModules` sample
(`src/samples/Teams/TaskModules` in microsoft/Agents-for-net), built on
`AgentApplication` + `TeamsAgentExtension`.

## What it demonstrates

Sending the agent any message returns a launcher Adaptive Card with four
buttons. Each button opens a task module (dialog) via a `task/fetch` invoke:

| Verb | Fetch | Submit |
|------|-------|--------|
| `simple_form` | Adaptive Card form (`simple-form-card.json`) | greets the name and closes |
| `webpage_dialog` | hosted webpage at `{APP_BASE_URL}/dialog-form` | greets name + email |
| `multi_step_form` | name card → `multi_step_form_submit_name` | email card → `multi_step_form_submit_email` → greets and closes |
| `mixed_example` | deep-link task module (`https://teams.microsoft.com/l/task/example-mixed`) | — |

Card definitions live in `src/resources/` and are loaded (with `{{token}}`
substitution) by `src/card_loader.py`, mirroring the .NET `CardLoader`.

> **Note:** task module verbs are read from `value.data.verb`, so the card
> `Action.Submit` payloads use a `verb` key (the .NET sample uses `task`).

## Webpage dialog

The `/dialog-form` route serves `src/resources/dialog-form.html`. It is exempt
from JWT authorization because Teams loads it in an iframe without a bearer
token. The page calls `microsoftTeams.dialog.url.submit(...)` which Teams
delivers back as a `task/submit` invoke with verb `webpage_dialog`.

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID` | Yes | — | Azure Bot / Entra app registration client ID |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET` | Yes | — | Client secret for the above registration |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID` | Yes | — | Entra tenant ID |
| `APP_BASE_URL` | No | `http://localhost:3978` | Public base URL of this agent. Used to build the webpage dialog URL (`{APP_BASE_URL}/dialog-form`). Teams loads that URL in an iframe, so it must be reachable from the internet — use your dev tunnel URL (e.g. `https://my-tunnel.devtunnels.ms`). |

## Running

1. Copy `env.TEMPLATE` to `.env` and fill in your Azure Bot registration
   (`CLIENTID`, `CLIENTSECRET`, `TENANTID`).
2. Set `APP_BASE_URL` to your dev tunnel URL (e.g.
   `APP_BASE_URL=https://my-tunnel.devtunnels.ms`) so Teams can load the
   **Webpage Dialog** task module in an iframe.
3. Install the SDK libraries (see the repository `README.md`).
4. Start the agent:

   ```bash
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`.
