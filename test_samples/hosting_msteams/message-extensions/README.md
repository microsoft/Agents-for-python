# Teams Message Extensions Sample

Python port of the .NET `MessageExtensions` sample
(`src/samples/Teams/MessageExtensions` in microsoft/Agents-for-net), built on
`AgentApplication` + `TeamsAgentExtension`.

## What it demonstrates

| Command | Decorator | Behaviour |
|---------|-----------|-----------|
| `searchQuery` | `@teams.message_extensions.query("searchQuery")` | Search command. On `initialRun` shows a hint; otherwise returns 5 Adaptive Card results, each with a tappable thumbnail preview. |
| select item | `@teams.message_extensions.select_item` | Handles a tap on a search result preview and returns a detail card. |
| `createCard` | `@teams.message_extensions.submit_action("createCard")` | Action command that builds a card from a submitted title/description. |
| link unfurling | `@teams.message_extensions.query_link` | Returns a preview card for a pasted link. |
| settings url | `@teams.message_extensions.query_setting_url` | Returns a config result pointing at `SETTINGS_URL`. |
| settings saved | `@teams.message_extensions.setting` | Handles applied settings (no-op on `CancelledByUser`). |
| fetch task | `@teams.message_extensions.fetch_action()` | Returns a "not implemented" task module dialog. |
| message | `@teams.activity("message")` | Echoes text and explains how to use the extension. |

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID` | Yes | — | Azure Bot / Entra app registration client ID |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET` | Yes | — | Client secret for the above registration |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID` | Yes | — | Entra tenant ID |
| `SETTINGS_URL` | No | `http://localhost:3978/settings` | Public URL of the settings page served by this agent. Teams loads this URL in the message-extension configuration pane, so it must be reachable from the internet — use your dev tunnel URL (e.g. `https://my-tunnel.devtunnels.ms/settings`). |

## Running

1. Copy `env.TEMPLATE` to `.env` and fill in your Azure Bot registration
   (`CLIENTID`, `CLIENTSECRET`, `TENANTID`).
2. If you want the **settings** command to work, set `SETTINGS_URL` to the
   `/settings` path on your dev tunnel (e.g.
   `SETTINGS_URL=https://my-tunnel.devtunnels.ms/settings`).
3. Install the SDK libraries (see the repository `README.md`).
4. Start the agent:

   ```bash
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`. Expose it with a
dev tunnel and side-load the app manifest into Teams to exercise the commands.
