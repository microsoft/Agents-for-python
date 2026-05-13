# Manually testing `on_search_query` in `message_extensions_agent.py`

The route is registered as `@TEAMS.message_extension.on_query("searchQuery")`, so
the manifest **commandId** and the Playground field must both say `searchQuery`.
The handler reads the parameter named `searchQuery` (and optionally `initialRun`).

## Two ways to test

| Path | Speed | What you need | Hits real Teams chrome? |
| --- | --- | --- | --- |
| **A. Agents Playground** | Fast (no Azure, no auth) | Local Playground CLI | No — simulator |
| **B. Real Teams via devtunnel** | Slower (needs Azure Bot + manifest sideload) | devtunnel, Azure Bot resource, `.zip` app manifest | Yes |

---

## Path A — Microsoft 365 Agents Playground (recommended for first pass)

### A1. One-time install (Windows)

```powershell
winget install --id=Microsoft.M365AgentsPlayground -e
```

### A2. Set the env and start the agent

```powershell
cd test_samples/teams_extension
copy env.TEMPLATE .env
# edit .env → fill CLIENTID/CLIENTSECRET/TENANTID (any valid Azure AD app reg works for Playground)
python message_extensions_agent.py
```

Confirm it logs `Listening on http://localhost:3978`.

### A3. Launch Playground pointed at the agent

In a second terminal:

```powershell
agentsplayground -e "http://localhost:3978/api/messages" -c "emulator"
```

This opens a browser-based chat that emulates Teams.

### A4. Trigger the search query

1. Click the **+** icon in the compose area → **Search Command**.
2. Click **Specify Command ID or Parameter** and enter:
   - **Command ID**: `searchQuery` ← must match the decorator argument
   - **Parameter name**: `searchQuery` ← what the handler reads from `query.parameters`
3. Type a search term (e.g. `pizza`) in the search field and press Enter.
4. Playground sends a `composeExtension/query` invoke. The Log Panel on the right shows the request and response payloads.
5. The five mock results (`Search Result 1` … `Search Result 5`) appear; the Python log prints `Search query received: pizza`.

### A5. Test the `initialRun` branch

Some clients send `initialRun=true` when the extension first opens. Playground
doesn't surface this directly, but you can hit it by:

- Restarting the agent.
- Opening the **Search Command** dropdown without typing — Playground auto-sends an empty query. To force `initialRun=true`, change the **Parameter name** field to `initialRun` and set its value to `true` (you'll need to send via the raw `Adaptive Card / Activity payload` panel if your Playground build supports it; otherwise verify this branch with a dedicated unit test that explicitly sets `initialRun=true` and validates the sample agent's behavior).

---

## Path B — Real Teams client (full end-to-end)

### B1. Tunnel localhost so Teams can reach it

```powershell
devtunnel user login
devtunnel create me-search -a
devtunnel port create -p 3978 me-search
devtunnel host me-search
```

Copy the `https://<tunnel-id>-3978.usw2.devtunnels.ms` URL.

### B2. Provision an Azure Bot resource

```powershell
az bot create -g <rg> -n <bot-name> --app-type SingleTenant --appid <client-id> --tenant-id <tenant-id> -e "https://<tunnel-id>-3978.usw2.devtunnels.ms/api/messages"
az bot msteams create -g <rg> -n <bot-name>
```

Use the same `<client-id>` / `<client-secret>` / `<tenant-id>` you put in `.env`.

### B3. Build the Teams app manifest

Create `manifest.json` somewhere with at least:

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "<a-fresh-guid>",
  "packageName": "com.example.searchext",
  "developer": {
    "name": "Test",
    "websiteUrl": "https://example.com",
    "privacyUrl": "https://example.com/privacy",
    "termsOfUseUrl": "https://example.com/terms"
  },
  "name": { "short": "Search Ext", "full": "Search Extension Sample" },
  "description": { "short": "Test on_search_query", "full": "Test on_search_query end-to-end" },
  "icons": { "color": "color.png", "outline": "outline.png" },
  "accentColor": "#0078D4",
  "composeExtensions": [
    {
      "botId": "<client-id>",
      "commands": [
        {
          "id": "searchQuery",
          "type": "query",
          "title": "Search",
          "description": "Search demo",
          "initialRun": true,
          "context": ["compose", "commandBox"],
          "parameters": [
            { "name": "searchQuery", "title": "Search query", "description": "Text to search", "inputType": "text" }
          ]
        }
      ]
    }
  ],
  "validDomains": ["<tunnel-id>-3978.usw2.devtunnels.ms"]
}
```

The two `searchQuery` strings — `commands[0].id` and `parameters[0].name` — are
what the route filters on. They must match the decorator arg (`"searchQuery"`)
and the parameter name read in the handler.

Add two square PNGs (`color.png` 192×192, `outline.png` 32×32 transparent) and
zip the three files together as `app.zip`.

### B4. Sideload and run

1. Teams → **Apps** → **Manage your apps** → **Upload an app** → **Upload a custom app** → pick `app.zip`.
2. Open any chat. Click the **+** below the compose box → pick **Search Ext**.
3. Type `pizza` → the five mock results render as a list of Adaptive Cards.
4. Tapping a result fires `composeExtension/selectItem` (handled by `on_select_item`) — a useful sanity check that the same wiring delivers two different invokes.

### B5. Inspect the wire traffic

- The Python log will show `Search query received: pizza` and `Item selected: 3:pizza` etc.
- The `devtunnel host` terminal prints every HTTP request — useful for confirming `composeExtension/query` arrives with `value.commandId = "searchQuery"` and `value.parameters[0].name = "searchQuery"`.

---

## Quick troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Selector doesn't fire | `commandId` mismatch — manifest `commands[0].id` ≠ decorator `"searchQuery"`. |
| Handler fires but `params` is empty | Parameter `name` in manifest ≠ what the handler reads (`searchQuery`). |
| 401 on `/api/messages` | `.env` client id/secret/tenant ≠ Azure Bot's app registration. |
| Pydantic `command_context` missing error | Real Teams always sends `commandContext`; Playground does too. If you're crafting raw payloads, include `"commandContext": "compose"`. |

---

## References

- [Debug message extension app in Microsoft 365 Agents Playground](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/debug-message-extension-app-in-test-tool)
- [Build Search-based Message Extensions](https://learn.microsoft.com/en-us/microsoftteams/platform/resources/messaging-extension-v3/search-extensions)
- [Respond to Search Command in Teams](https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/search-commands/respond-to-search)
- [Define Search Command](https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/search-commands/define-search-command)
- [Test your agent locally in Microsoft 365 Agents Playground](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/test-with-toolkit-project)
