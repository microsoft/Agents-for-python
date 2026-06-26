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

## Running

1. Copy `env.TEMPLATE` to `.env` and fill in your Azure Bot registration
   (`CLIENTID`, `CLIENTSECRET`, `TENANTID`). Optionally set `SETTINGS_URL`.
2. Install the SDK libraries (see the repository `README.md`).
3. Start the agent:

   ```bash
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`. Expose it with a
dev tunnel and side-load the app manifest into Teams to exercise the commands.
