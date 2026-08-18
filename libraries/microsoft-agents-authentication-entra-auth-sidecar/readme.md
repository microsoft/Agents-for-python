# Microsoft Agents Entra ID Auth Sidecar Authentication

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-authentication-entra-auth-sidecar)](https://pypi.org/project/microsoft-agents-authentication-entra-auth-sidecar/)

This library integrates the **Microsoft 365 Agents SDK for Python** with the **Microsoft
Entra ID Agent Container** (the *sidecar*). Instead of acquiring tokens directly with MSAL,
the SDK delegates token acquisition to the sidecar's HTTP API, so the agent process never
handles secrets, certificates, or keys.

## Release Notes

<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>1.3.0</td>
    <td>2026-07-30</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v130">
        1.3.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.2.0</td>
    <td>2026-07-17</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v120">
        1.2.0 Release Notes
      </a>
    </td>
  </tr>
</table>

## Packages Overview

We offer the following PyPI packages to create conversational experiences based on Agents:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-activity` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/) | Types and validators implementing the Activity protocol spec. |
| `microsoft-agents-hosting-core` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/) | Core library for Microsoft Agents hosting. |
| `microsoft-agents-hosting-aiohttp` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/) | Configures aiohttp to run the Agent. |
| `microsoft-agents-hosting-fastapi` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-fastapi)](https://pypi.org/project/microsoft-agents-hosting-fastapi/) | Configures fastapi to run the Agent. |
| `microsoft-agents-hosting-msteams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-hosting-dialogs` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/) | Dialog system with waterfall dialogs, prompts, and multi-turn conversation management. |
| `microsoft-agents-hosting-slack` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/) | Provides classes to host an Agent for Slack. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |
| `microsoft-agents-authentication-entra-auth-sidecar` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-entra-auth-sidecar)](https://pypi.org/project/microsoft-agents-authentication-entra-auth-sidecar/) | Credential-free Entra ID Agent ID authentication via the sidecar. | 

## Why a sidecar?

- **Credential-free agent code** — all credential management (Managed Identity, Workload
  Identity, Key Vault certs, client secret for dev) lives in the sidecar.
- **Language-agnostic** — every language SDK talks to the same simple HTTP API.
- **Consistent local/prod** — the same container runs locally (Docker) and in production.

## Installation

```bash
pip install microsoft-agents-authentication-entra-auth-sidecar
```

## Components

| Type | Role |
|---|---|
| `SidecarAuth` | Token provider implementing `AccessTokenProviderBase`. Translates each SDK token call into a sidecar request and serves repeat requests from an in-memory token cache. |
| `SidecarHttpClient` | HTTP client for the sidecar API. Builds query strings, parses `{ "authorizationHeader": "Bearer <token>" }` responses, retries transient failures, and validates the base URL (SSRF safety). |
| `SidecarConnectionSettings` | Configuration model carrying `service_name`, `blueprint_service_name`, `scopes`, `sidecar_base_url`, `request_timeout`, `retry_count`, and `bypass_local_network_restriction`. |

## Usage

Use the generic `ConnectionManager` from `microsoft-agents-hosting-core` with
`provider_factory=SidecarAuth` — no sidecar-specific connection manager is required:

```python
from microsoft_agents.hosting.core import ConnectionManager
from microsoft_agents.authentication.entra_auth_sidecar import SidecarAuth

connection_manager = ConnectionManager(
    provider_factory=SidecarAuth,
    CONNECTIONS={
        "SERVICE_CONNECTION": {
            "SETTINGS": {
                "AUTHTYPE": "EntraAuthSideCar",
                "CLIENTID": "<blueprint-app-id>",
            }
        }
    },
    CONNECTIONSMAP=[{"SERVICEURL": "*", "CONNECTION": "SERVICE_CONNECTION"}],
)
```

## Sidecar endpoint mapping

The provider uses the sidecar's unauthenticated endpoint, where `{serviceName}` is a
downstream API configured in the sidecar:

```
GET /AuthorizationHeaderUnauthenticated/{serviceName}
    ?AgentIdentity={agentAppInstanceId}
    &AgentUserId={agentUserObjectId}        (delegated/agentic-user flow, GUID)
    &AgentUsername={agentUserUpn}           (delegated/agentic-user flow, UPN)
    &optionsOverride.Scopes={scope}         (repeatable)
    &optionsOverride.RequestAppToken=true   (app-only flow)
    &optionsOverride.AcquireTokenOptions.Tenant={tenantId}
```

| `AccessTokenProviderBase` method | Sidecar call |
|---|---|
| `get_agentic_application_token` | `blueprint_service_name` (default `agenticblueprint`) with `AgentIdentity`. Returns the Blueprint token. |
| `get_agentic_instance_token` | `service_name` with `AgentIdentity` + `RequestAppToken=true`. App-only resource token (returned as a tuple for SDK compatibility). |
| `get_agentic_user_token` | `service_name` with `AgentIdentity` + `AgentUserId`/`AgentUsername`. Resource token for the agentic user. |
| `get_access_token` | `service_name` with `RequestAppToken=true`. App-only connection token. |

`AgentUserId` (object id) and `AgentUsername` (UPN) are mutually exclusive; the client emits
exactly one and rejects a request that sets both.

> **Note:** the sidecar performs the entire agentic identity chain
> (Blueprint → Instance → agentic User via federated identity) internally and returns the
> final resource token, so the SDK only translates each call into a single sidecar request.

## Configuration

| Setting | Required | Default | Description |
|---|---|---|---|
| `SERVICE_NAME` | No | `default` | Downstream API name configured in the sidecar. |
| `BLUEPRINT_SERVICE_NAME` | No | `agenticblueprint` | Downstream API name for the Blueprint token-exchange step. Must be configured app-only with the `api://AzureAdTokenExchange/.default` scope on the sidecar. |
| `SCOPES` | No | — | Scope overrides forwarded as `optionsOverride.Scopes`. |
| `SIDECAR_BASE_URL` | No | `http://localhost:5178` | Sidecar endpoint. Resolution: `SIDECAR_URL` env var > this > default. The resolved host must be loopback/private unless `BYPASS_LOCAL_NETWORK_RESTRICTION` is set. |
| `BYPASS_LOCAL_NETWORK_RESTRICTION` | No | `false` | **UNSAFE.** Disables the loopback/private-address SSRF safety check. Only enable for a carefully validated private-network configuration. |
| `REQUEST_TIMEOUT` | No | `30` (seconds) | Per-attempt HTTP timeout for sidecar calls. |
| `RETRY_COUNT` | No | `3` | Retry attempts for transient failures (HTTP 408/429/5xx, network errors, timeouts) using exponential backoff. `0` disables retries. |

### Base URL resolution

1. `SIDECAR_URL` environment variable
2. Explicit configuration (`SIDECAR_BASE_URL`)
3. `http://localhost:5178` (default — the Entra ID Agent Container's local default port)

### Loopback/private-address safety check (SSRF)

Because the sidecar issues tokens for the agent's identity, the provider refuses to send
requests to an arbitrary host. After resolution, the base URL **must** point to a loopback
(`localhost`, `127.0.0.0/8`, `::1`) or private address (RFC 1918 / RFC 4193 / link-local). A
public/routable address is rejected. To intentionally target a non-private address, set
`BYPASS_LOCAL_NETWORK_RESTRICTION` to `true` (UNSAFE — only for validated private networks).

## Token caching

`SidecarAuth` keeps a lightweight in-memory token cache so repeated calls for the same
identity don't hit the sidecar on every turn:

- **Key** — the agent identity plus the other request parameters that change the issued
  token (downstream service name, user, tenant, app-only vs. user, normalized scopes).
- **Lifetime** — the token's own JWT `exp` claim when parseable, otherwise a conservative
  5-minute fallback. An entry is evicted once within 30 seconds of expiry.
- **Force refresh** — `get_access_token(..., force_refresh=True)` evicts the entry and
  re-acquires from the sidecar.

## Key Classes

- **`SidecarAuth`** — token provider implementing `AccessTokenProviderBase`
- **`SidecarHttpClient`** — HTTP client for the sidecar API

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
