# BizChat SSO Sample – Issue #294 Reproduction

This sample reproduces [issue #294](https://github.com/microsoft/Agents-for-python/issues/294): the SSO consent flow failing with HTTP 400 in BizChat (Microsoft 365 Chat / M365 Copilot) when admin consent has **not** been pre-granted for the OAuth connection.

When the bug is present, typing `profile` in BizChat surfaces an unhandled `ClientResponseError: 400 Bad Request` from the token exchange endpoint instead of prompting the user to consent.

---

## Prerequisites

- Python 3.10+
- An **Azure subscription** with permissions to create App Registrations and Bot resources
- Access to the **Microsoft 365 admin center** (to publish the agent as a Copilot extension)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) (optional, for provisioning)
- [Microsoft Dev Tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started) (for local testing)

---

## Step 1 – Create the Azure App Registration

1. Go to the [Azure portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Give it a name (e.g., `BizChatSSOSample`).
3. Under **Supported account types**, choose **Accounts in this organizational directory only**.
4. Click **Register**.
5. Note the **Application (client) ID** and **Directory (tenant) ID** – you'll need them later.
6. Go to **Certificates & secrets** → **New client secret**, copy the value immediately.
7. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated** → add **User.Read**. Click **Grant admin consent** if you want to test the **happy path** first; skip this step to reproduce the bug.
8. Go to **Expose an API** → set the **Application ID URI** to `api://<client-id>`.
9. Under **Expose an API** → **Add a scope**:
   - Scope name: `access_as_user`
   - Who can consent: **Admins and users**
   - Display/description: anything descriptive
   - Click **Add scope**.
10. Under **Expose an API** → **Add a client application**, add the M365 first-party client IDs that BizChat uses:
    - `1fec8e78-bce4-4aaf-ab1b-5451cc387264` (Teams mobile/desktop)
    - `5e3ce6c0-2b1f-4285-8d4b-75ee78787346` (Teams web)
    - `4765445b-32c6-49b0-83e6-1d93765276ca` (Microsoft 365 web)
    - `0ec893e0-5785-4de6-99da-4ed124e5296c` (Microsoft 365 desktop)
    - `d3590ed6-52b3-4102-aeff-aad2292ab01c` (Microsoft Office)
    - `bc59ab01-8403-45c6-8796-ac3ef710b3e3` (Outlook)
    - `27922004-5251-4030-b22d-91ecd9a37ea4` (Outlook mobile)

---

## Step 2 – Create the Azure Bot Resource

1. In the Azure portal search for **Azure Bot** and click **Create**.
2. Choose **Multi Tenant** type (or **Single Tenant** matching your app registration tenant).
3. Under **Microsoft App ID**, select **Use existing app registration** and provide the client ID from Step 1.
4. Complete provisioning and open the bot resource.
5. Go to **Configuration** and note the **Messaging endpoint** field – you will fill it in after setting up the tunnel.

---

## Step 3 – Configure the OAuth Connection

1. In the Azure Bot resource, go to **Configuration** → **Add OAuth Connection Settings**.
2. Fill in:
   - **Name**: choose a name, e.g., `GraphConnection` (this goes in `env` as the connection name)
   - **Service provider**: **Azure Active Directory v2**
   - **Client ID**: same as Step 1
   - **Client Secret**: same as Step 1
   - **Token Exchange URL**: `api://<client-id>/access_as_user`
   - **Tenant ID**: your tenant ID
   - **Scopes**: `User.Read`
3. Save the connection.

> **To reproduce issue #294**: do **not** grant admin consent for the app registration's API permissions (`User.Read`). When a user without prior consent tries to sign in through BizChat, the token exchange endpoint returns HTTP 400 and the bug is triggered.
>
> **To test the fixed path**: grant admin consent via **API permissions → Grant admin consent** in the app registration.

---

## Step 4 – Set Up a Dev Tunnel

```bash
# Install dev tunnels (Windows)
winget install Microsoft.devtunnel

# Authenticate
devtunnel user login

# Create a persistent tunnel
devtunnel create bizchat-sso -a
devtunnel port create -p 3978 bizchat-sso
devtunnel host -a bizchat-sso
```

Copy the public tunnel URL (format: `https://<id>-3978.use.devtunnels.ms`).

In the Azure Bot resource → **Configuration**, set the **Messaging endpoint** to:
```
https://<your-tunnel-id>-3978.use.devtunnels.ms/api/messages
```

---

## Step 5 – Configure and Run the Sample

```bash
# From the repo root, activate your virtual environment
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install SDK packages in editable mode (if not done already)
pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat

# Install sample dependencies
pip install python-dotenv aiohttp

cd test_samples/bizchat_sso
cp env.TEMPLATE .env
```

Edit `.env` and fill in your values:

```env
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=<client-id from Step 1>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=<client-secret from Step 1>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=<tenant-id from Step 1>

AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=GraphConnection
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__OBOCONNECTIONNAME=GraphConnection
```

Run the agent:

```bash
python bizchat_sso_agent.py
```

The server starts on `http://localhost:3978/api/messages`.

---

## Step 6 – Publish the Agent to M365 BizChat

You have two options for testing in BizChat:

### Option A – M365 Agents Playground (recommended for local dev)

1. Install the [M365 Agents Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit):
   ```bash
   winget install --id=Microsoft.M365AgentsPlayground -e
   ```
2. Open Agents Playground and add a new agent pointing to your tunnel URL + `/api/messages`.
3. Use the BizChat channel option to simulate BizChat behavior.

### Option B – Publish as a Teams/M365 App

1. Create an app manifest (`manifest.json`) targeting your bot:
   ```json
   {
     "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
     "manifestVersion": "1.16",
     "id": "<app-guid>",
     "version": "1.0.0",
     "name": { "short": "BizChat SSO Sample" },
     "description": { "short": "Reproduces issue #294", "full": "SSO consent flow repro" },
     "icons": { "color": "color.png", "outline": "outline.png" },
     "accentColor": "#FFFFFF",
     "bots": [
       {
         "botId": "<client-id from Step 1>",
         "scopes": ["personal"],
         "isNotificationOnly": false,
         "supportsCalling": false,
         "supportsVideo": false,
         "supportsFiles": false
       }
     ],
     "permissions": ["identity", "messageTeamMembers"],
     "validDomains": ["<your-tunnel-id>-3978.use.devtunnels.ms"]
   }
   ```
2. Sideload the app in the Microsoft Teams admin center or via the Teams client.
3. Once installed in Teams personal scope, open **M365 Copilot / BizChat** – the agent will appear under **Agents**.

---

## Step 7 – Reproduce the Bug

1. Open BizChat (go to [microsoft365.com](https://microsoft365.com) → **Copilot** or press the Copilot button in M365 apps).
2. Open the agent (it appears in the **Agents** panel on the right).
3. Type `profile`.

**With the bug (no admin consent):**
- BizChat sends a `signin/tokenExchange` invoke.
- The SDK calls the token exchange endpoint.
- The endpoint returns HTTP 400 (consent required).
- The agent logs: `ClientResponseError: 400 Bad Request, url=https://api.botframework.com/api/usertoken/exchange?...`
- The error handler sends back: `An error occurred: ClientResponseError: 400 Bad Request`

**With the fix applied:**
- The SDK catches the 400 and treats it as "consent required".
- BizChat shows a sign-in card allowing the user to grant consent.
- After consent, the flow resumes and `profile` returns your Graph profile.

---

## Observing the Fix

The fix lives in:
```
libraries/microsoft-agents-hosting-core/microsoft_agents/hosting/core/_oauth/_oauth_flow.py
```

Method `_continue_from_invoke_token_exchange` – it now catches HTTP 400/412 responses from the token exchange endpoint and signals "consent required" back to the flow instead of propagating the exception.

---

## Sample Commands

| Command | Description |
|---------|-------------|
| `profile` | Trigger SSO and display your Microsoft Graph profile |
| `logout` | Sign out and clear the cached token |
| anything else | Echo the message back |
