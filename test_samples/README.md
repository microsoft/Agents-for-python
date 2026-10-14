# Python SDK test samples

This directory contains runnable examples, compatibility ports, and tests for
the Microsoft Agents SDK for Python. Start with the linked sample guide when
one is available; it has the most specific setup and configuration details.
Unless stated otherwise, run commands from the sample directory.

## Common setup

- Python samples generally require Python 3.10 or later. Check the sample
  guide for any additional version or service requirements.
- From the repository root, create and activate a virtual environment, then
  install the repository's SDK libraries:

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  .\scripts\dev_setup.ps1
  ```

  On Linux or macOS, activate with `source .venv/bin/activate` and run
  `./scripts/dev_setup.sh`.
- When a sample has a `requirements.txt`, install it from the repository root,
  for example:
  `python -m pip install -r test_samples/proactive/requirements.txt`.
  For samples with a `pyproject.toml`, follow that sample's `uv sync`
  instructions instead.
- Where an `env.TEMPLATE` is provided, copy it to `.env` and fill in the
  sample's required settings. Do not commit credentials. Most bot-hosted
  samples need an Azure Bot/Entra app registration; Teams invoke features may
  also need Teams and a public development tunnel. OAuth, Graph, and cloud
  identity examples have additional requirements noted below or in their
  guides.

The distribution names in this repository's `libraries/` projects are
`microsoft-agents-activity`,
`microsoft-agents-authentication-entra-auth-sidecar`,
`microsoft-agents-authentication-msal`,
`microsoft-agents-copilotstudio-client`,
`microsoft-agents-hosting-aiohttp`,
`microsoft-agents-hosting-core`,
`microsoft-agents-hosting-dialogs`,
`microsoft-agents-hosting-fastapi`,
`microsoft-agents-hosting-msteams`,
`microsoft-agents-hosting-teams`,
`microsoft-agents-storage-blob`,
`microsoft-agents-storage-cosmos`, and
`microsoft-agents-testing`. Use a sample's requirements or project setup to
select the needed packages; not every sample needs every library.

## Agent and channel samples

| Sample | Purpose and additional prerequisites | Run / details |
| --- | --- | --- |
| [`app_style/`](app_style/README.md) | App-style aiohttp agents: empty, authorization, Copilot Studio, proactive echo, and streaming examples. Configure the credentials/connections needed by the selected agent. | From `test_samples/app_style`: `python empty_agent.py`, `python authorization_agent.py`, `python mcs_agent.py`, `python echo_proactive_agent.py`, or `python streaming_agent.py`. |
| [`fastapi/`](fastapi/README.md) | FastAPI versions of the empty and authorization agents; the authorization example uses Microsoft Graph and GitHub. | From `test_samples/fastapi`: `python empty_agent.py` or `python authorization_agent.py`. |
| [`cards/`](cards/README.md) | Adaptive Cards, submit/execute actions, dynamic search, and media cards. `Action.Execute` and dynamic search require Teams. | From `test_samples/cards`: `python agent.py`. |
| [`handling_attachments/`](handling_attachments/README.md) | Sends and receives inline, URL, and uploaded attachments; uploaded attachments require Teams. | From `test_samples/handling_attachments`: `python -m src.main`. |
| [`proactive/`](proactive/README.md) | Proactive conversation continuation, stored references, OAuth, and an external notification endpoint. Requires an Azure Bot OAuth connection and a tunnel or Teams/Agents Playground for interaction. | From the repository root: `python test_samples/proactive/proactive_agent.py`. |
| [`agentic-test/`](agentic-test/) | Acquires an agentic user token and displays token claims in an Adaptive Card. Requires the configured `AGENTIC` authentication connection. | From `test_samples/agentic-test`: `python src/main.py`; install `requirements.txt` first. |
| [`copilot_studio_client_sample/`](copilot_studio_client_sample/app.py) | Console client for a Copilot Studio agent using MSAL interactive sign-in and the Copilot Studio client library. Requires a configured Entra app and Copilot Studio connection. | `python app.py`. No sample README or `requirements.txt` is present; install its SDK and MSAL dependencies in the environment. |
| [`copilot_studio_connector/`](copilot_studio_connector/README.md) | Receives Copilot Studio connector requests and uses OAuth/OBO to call Graph. Requires an Azure Bot app, Copilot Studio connector, and Graph OAuth permissions. | From `test_samples/copilot_studio_connector`: `pip install -r requirements.txt`, then `python app.py`. |
| [`compat/weather-agent-open-ai/`](compat/weather-agent-open-ai/app.py) | Compatibility weather agent backed by Azure OpenAI. Requires Azure OpenAI configuration as well as bot credentials. | From `test_samples/compat/weather-agent-open-ai`: install `requirements.txt`, then `python app.py`. |
| [`extensions/extension-starter/`](extensions/extension-starter/README.md) | Minimal example of extending the SDK; the guide recommends Microsoft 365 Agents Playground for interaction. | From `test_samples/extensions/extension-starter`: `python -m src.sample.main`. |
| [`tethered-agent/`](tethered-agent/src/main.py) | Echo agent using `tethered` to limit outbound network access to the configured login and Bot Framework hosts. Requires the normal agent configuration and the `tethered` dependency. | From `test_samples/tethered-agent`: `python -m src.main`. The directory's README is empty; the entry point and purpose are identified from the source. |

## Teams samples

| Sample | Purpose and additional prerequisites | Run / details |
| --- | --- | --- |
| [`hosting_msteams/conversation-agent/`](hosting_msteams/conversation-agent/README.md) | Teams conversation lifecycle events, member lookups, mentions, and proactive messages. Requires a Teams app and bot registration. | From the sample directory: `python -m src.main`. |
| [`hosting_msteams/graph-clients/`](hosting_msteams/graph-clients/README.md) | Teams commands using app-only and delegated Microsoft Graph clients; requires Graph application/delegated permissions and consent. | From the sample directory: `python -m src.main`. |
| [`hosting_msteams/message-extensions/`](hosting_msteams/message-extensions/README.md) | Teams message-extension search, actions, link previews, and settings. Requires a Teams app and a reachable tunnel for settings. | From the sample directory: `python -m src.main`. |
| [`hosting_msteams/task-modules/`](hosting_msteams/task-modules/README.md) | Teams task modules with card forms, a webpage dialog, and multi-step submits. Requires a Teams app and a reachable tunnel for the webpage dialog. | From the sample directory: `python -m src.main`. |
| [`teams_extension/`](teams_extension/README.md) | Three `TeamsAgentExtension` examples: message extensions, task modules, and meeting events. Requires Teams; install `microsoft-teams-api` as described in the guide. | From `test_samples/teams_extension`, run `python message_extensions_agent.py`, `python task_modules_agent.py`, or `python meeting_events_agent.py`. |

## Authentication and cloud identity

| Sample | Purpose and additional prerequisites | Run / details |
| --- | --- | --- |
| [`entra_sidecar/`](entra_sidecar/README.md) | Credential-free outbound token acquisition through the Entra ID Agent Container sidecar. Requires the sidecar and its downstream API configuration. | Follow the guide to install requirements and run `python agent.py` from `test_samples/entra_sidecar`. |

## Compatibility samples

| Sample | Purpose | Run / details |
| --- | --- | --- |
| [`compat/dialogs/complex_dialog/`](compat/dialogs/complex_dialog/README.md) | BotBuilder complex-dialog port. | From the sample directory: install `requirements.txt`, then run `python -m src.main`. |
| [`compat/dialogs/custom_dialogs/`](compat/dialogs/custom_dialogs/README.md) | BotBuilder custom-dialogs port. | From the sample directory: install `requirements.txt`, then run `python -m src.main`. |
| [`compat/dialogs/multi_turn/`](compat/dialogs/multi_turn/README.md) | BotBuilder multi-turn-prompt port. | From the sample directory: install `requirements.txt`, then run `python -m src.main`. |
| [`compat/dialogs/oauth_prompt/`](compat/dialogs/oauth_prompt/README.md) | OAuth prompt sample. Requires an Azure Bot OAuth connection. | From the sample directory: install `requirements.txt`, then run `python -m src.main`. |
| [`compat/dialogs/user_auth/`](compat/dialogs/user_auth/README.md) | User-authentication sample that accesses Graph; requires the corresponding OAuth connection and permissions. | From the sample directory: install `requirements.txt`, then run `python -m src.main`. |
| [`compat/teams_agent/`](compat/teams_agent/app.py) | Legacy Teams handler examples for SSO and other Teams features. | Purpose is identifiable from the source, but a runnable command could not be verified: its imports reference `test_samples.activity_handler`, which is not present here. |
| [`compat/agent_to_agent/`](compat/agent_to_agent/) | Two-agent channel/agent communication example. | The source imports also reference `test_samples.activity_handler`; a runnable command could not be verified against this checkout. |

## Observability and testing

| Sample | Purpose and prerequisites | Run / test |
| --- | --- | --- |
| [`otel/quickstart/`](otel/quickstart/README.md) | In-code OpenTelemetry configuration and instrumentation; `uv` and the configured agent connections are required. | In the sample directory: `uv sync`, then `uv run python -m src.main`. The guide also starts the Aspire dashboard with `.\start_dashboard.ps1`. |
| [`otel/zero-code/`](otel/zero-code/README.md) | OpenTelemetry auto-instrumentation configured through environment variables; `uv` and the configured agent connections are required. | In the sample directory: `uv sync`, then run `.\start_dashboard.ps1` and `.\start_agent.ps1`. |
| [`testing/`](testing/README.md) | Tests an `AgentApplication` in memory with `TestAdapter` and `TestFlow`; no live server is needed for the tests. | From `test_samples/testing`: `uv sync` then `uv run pytest`. To run the aiohttp host, use `uv run python src/app.py`. |
