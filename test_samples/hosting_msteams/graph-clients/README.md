# Teams Graph Clients Sample

Demonstrates creating and using Microsoft Graph clients from Teams route
handlers:

| Command | Graph client | Endpoint |
|---------|--------------|----------|
| `/appgraph apps` | app-only client | `GET /applications?$top=1&$select=id,appId,displayName` |
| `/usergraph me` | delegated user client | `GET /me?$select=id,displayName,userPrincipalName,mail` |
| `/signout` | delegated user auth handler | signs out the `GRAPH` handler |

## Permissions

The app-only command uses the service connection credentials and requires
Microsoft Graph application permissions such as `Application.Read.All` with
admin consent.

The user command uses the configured Azure Bot OAuth connection and requires
delegated Microsoft Graph permissions such as `User.Read`.

## Running

1. Copy `env.TEMPLATE` to `.env`.
2. Fill in your bot/app credentials and configure the `GRAPH` OAuth connection.
3. Start the sample:

   ```powershell
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`. Expose it with a
dev tunnel and side-load the app manifest into Teams.
