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

## Running

1. Copy `env.TEMPLATE` to `.env` and fill in your Azure Bot registration
   (`CLIENTID`, `CLIENTSECRET`, `TENANTID`). Set `APP_BASE_URL` to your public
   (dev tunnel) URL so the webpage dialog loads.
2. Install the SDK libraries (see the repository `README.md`).
3. Start the agent:

   ```bash
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`.
