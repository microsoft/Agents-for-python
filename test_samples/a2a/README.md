# A2A echo sample

This sample defines a custom Microsoft 365 Agents SDK agent, adds A2A
capabilities, and hosts it with FastAPI.

## Install

From this directory:

```powershell
pip install -r requirements.txt
```

When developing from this repository, install the SDK libraries in editable
mode using `scripts\dev_setup.ps1`.

## Run the agent

From the repository root:

```powershell
python -m test_samples.a2a.agent.main
```

The server listens on `http://127.0.0.1:41241` by default. Its endpoints are:

- Agent card: `http://127.0.0.1:41241/a2a/.well-known/agent-card.json`
- JSON-RPC: `http://127.0.0.1:41241/a2a`
- Health check: `http://127.0.0.1:41241/health`

Set `HOST` or `PORT` to override the defaults.

## Run the client

In another terminal:

```powershell
python -m test_samples.a2a.client.cli --url http://127.0.0.1:41241/a2a
```

Enter a message to receive an echo response. Type `/quit` to exit.

JWT authorization is intentionally disabled for this local sample. Production
applications should configure an `AgentAuthConfiguration` and enable the A2A
JWT middleware.