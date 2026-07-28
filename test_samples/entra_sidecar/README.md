# Entra ID Auth Sidecar Sample

This sample shows how to wire the **credential-free** Entra ID Agent Container (sidecar)
authentication provider into an agent. Token acquisition is delegated to the sidecar's HTTP
API, so the agent process never handles secrets, certificates, or keys.

## How it works

The sample uses the generic `ConnectionManager` from `microsoft-agents-hosting-core` with
`provider_factory=SidecarAuth`:

```python
from microsoft_agents.hosting.core import ConnectionManager
from microsoft_agents.authentication.entra_auth_sidecar import SidecarAuth

CONNECTION_MANAGER = ConnectionManager(provider_factory=SidecarAuth, **agents_sdk_config)
```

No `SidecarConnectionManager` is needed — the generic connection manager dispatches to any
`AccessTokenProviderBase` implementation.

## Prerequisites

- The **Microsoft Entra ID Agent Container (sidecar)** running and reachable (default
  `http://localhost:5178`). See the
  [Entra ID Agent Container local development guide](https://learn.microsoft.com/en-us/entra/agent-id/sidecar-local-development).
- The sidecar must declare matching **downstream APIs** (mirrors the C# `SidecarAuth` sample):

  | Downstream API name | Used by | Configuration |
  |---|---|---|
  | `botframework` | `ServiceConnection` (channel callbacks) | Scope `5a807f24-c9de-44ee-a3a7-329e88a00ffc/.default` |
  | `agenticblueprint` | `get_agentic_application_token` | App-only (`RequestAppToken`), scope `api://AzureAdTokenExchange/.default` |

## Setup

1. Copy `env.TEMPLATE` to `.env` and fill in your blueprint app id and scopes.
2. Install the dependencies (from the repository root, with your venv active):

   ```bash
   pip install -r test_samples/entra_sidecar/requirements.txt
   ```

   The SDK libraries (including `microsoft-agents-authentication-entra-auth-sidecar`)
   are also installed by the repository dev setup script (`scripts/dev_setup.ps1` /
   `scripts/dev_setup.sh`). If you set up your environment before this sample was added,
   re-run that script or `pip install -e ./libraries/microsoft-agents-authentication-entra-auth-sidecar/`.
3. Run the agent:

   ```bash
   python agent.py
   ```

The agent listens on `http://localhost:3978/api/messages` (override with `HOST`/`PORT`).
A sidecar-reachability probe is exposed at `http://localhost:3978/health` (mirrors the C#
sample's `/health` endpoint; returns 200 when the sidecar is reachable, 503 otherwise).

## Configuration

| Setting | Default | Description |
|---|---|---|
| `AUTHTYPE` | — | `EntraAuthSideCar` |
| `CLIENTID` | — | Agent (blueprint) app registration client ID. Used as the inbound-token audience and the blueprint app id. |
| `TENANTID` | — | Entra tenant ID used to validate **inbound** channel tokens. Required only when `TOKENVALIDATION__ENABLED=true`. |
| `TOKENVALIDATION__ENABLED` | `false` | Enable inbound channel-token validation. Off by default for local dev (parity with the C# `TokenValidation:Enabled`). Set `true` for non-local deployments. |
| `SERVICE_NAME` | `default` | Downstream API name configured in the sidecar (this sample uses `botframework`) |
| `BLUEPRINT_SERVICE_NAME` | `agenticblueprint` | Blueprint token-exchange downstream API |
| `SIDECAR_BASE_URL` | `http://localhost:5178` | Sidecar endpoint (`SIDECAR_URL` env var takes precedence) |
| `BYPASS_LOCAL_NETWORK_RESTRICTION` | `false` | **UNSAFE.** Disables the SSRF loopback/private check |
| `REQUEST_TIMEOUT` | `30` | Per-attempt HTTP timeout (seconds) |
| `RETRY_COUNT` | `3` | Retry attempts for transient sidecar failures |

## Troubleshooting

**`HTTP Error 400: Bad Request` from `jwt/jwks_client.py` when a message arrives**
This is **inbound** token validation failing before the sidecar is ever called. The middleware
tries to fetch signing keys for your tenant; a 400 means the keys URL is invalid — typically
because `TENANTID` is missing/placeholder, or the inbound token's issuer requires a real tenant.

- **Local development:** leave `TOKENVALIDATION__ENABLED=false` (the default). The sample then
  injects anonymous claims and skips inbound validation entirely, matching the C# sample's
  Development behavior (`TokenValidation:Enabled=false`).
- **Non-local deployment:** set `TOKENVALIDATION__ENABLED=true` and provide a real
  `CLIENTID` (audience) and `TENANTID`.

> Note: credential-free applies to **outbound** token acquisition (the sidecar owns those
> secrets). Validating **inbound** channel tokens is a separate concern controlled by
> `TOKENVALIDATION__ENABLED`.

