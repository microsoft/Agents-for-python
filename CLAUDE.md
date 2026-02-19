# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Microsoft 365 Agents SDK for Python**, a framework for building enterprise-grade conversational agents for M365, Teams, Copilot Studio, and other platforms. The SDK replaces the legacy Bot Framework SDK (botbuilder packages) with a modern, modular architecture.

**Important**: Python imports use underscores (`microsoft_agents`), not dots (`microsoft.agents`).

## Development Setup

### Initial Setup

**Quick setup (Linux/macOS)**:
```bash
. ./scripts/dev_setup.sh
```

**Quick setup (Windows)**:
```bash
. ./scripts/dev_setup.ps1
```

**Manual setup** (from repository root):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all libraries in editable mode
pip install -e ./libraries/microsoft-agents-activity/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-copilotstudio-client/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-teams/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-blob/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-cosmos/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-fastapi/ --config-settings editable_mode=compat

# Install development dependencies
pip install -r dev_dependencies.txt

# Setup pre-commit hooks
pre-commit install
```

**Python version**: Requires Python 3.10+, supports 3.10-3.14. Recommended: Python 3.11+

## Common Commands

### Testing

```bash
# Run all tests
pytest

# Run tests in a specific directory
pytest tests/microsoft-agents-activity/

# Run a single test file
pytest tests/microsoft-agents-activity/test_activity.py

# Run a single test
pytest tests/microsoft-agents-activity/test_activity.py::test_activity_creation

# Run with verbose output
pytest -v

# Run with test markers
pytest -m unit
pytest -m integration
pytest -m slow
```

### Code Quality

```bash
# Format code with black (line length: 88)
black libraries/

# Check formatting without making changes
black libraries/ --check

# Lint with flake8 (max line length: 127, max complexity: 10)
flake8 .

# Run pre-commit checks manually
pre-commit run --all-files
```

### Building Packages

```bash
# Set package version (from versioning directory)
cd ./versioning
setuptools-git-versioning

# Build all packages (run from repository root)
mkdir -p dist
for dir in libraries/*; do
  if [ -f "$dir/pyproject.toml" ]; then
    (cd "$dir" && python -m build --outdir ../../dist)
  fi
done

# Build a specific package
cd libraries/microsoft-agents-activity
python -m build
```

## Architecture Overview

### Layer Structure

The SDK follows a **layered, modular architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Web Framework Adapters                                 │
│ hosting-aiohttp, hosting-fastapi                                │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Platform Extensions & Storage                          │
│ hosting-teams, storage-blob, storage-cosmos                     │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Authentication                                          │
│ authentication-msal                                              │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Core Hosting Engine                                    │
│ hosting-core (Agent, TurnContext, State, Routing)              │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: Protocol/Schema                                        │
│ activity (Activity protocol, Pydantic models)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Package Dependencies

Each library in `libraries/` is independently published to PyPI:

| Package | Purpose | Key Abstractions |
|---------|---------|------------------|
| `microsoft-agents-activity` | Activity protocol types using Pydantic | `Activity`, `ConversationReference`, protocols |
| `microsoft-agents-hosting-core` | Core agent runtime and lifecycle | `Agent`, `TurnContext`, `ActivityHandler`, `AgentApplication` |
| `microsoft-agents-authentication-msal` | MSAL-based OAuth authentication | `MsalAuth`, `MsalConnectionManager` |
| `microsoft-agents-hosting-aiohttp` | aiohttp web framework adapter | `CloudAdapter`, `start_agent_process()` |
| `microsoft-agents-hosting-fastapi` | FastAPI web framework adapter | `CloudAdapter`, `start_agent_process()` |
| `microsoft-agents-hosting-teams` | Teams-specific extensions | `TeamsActivityHandler`, `TeamsInfo` |
| `microsoft-agents-storage-blob` | Azure Blob Storage persistence | `BlobStorage` |
| `microsoft-agents-storage-cosmos` | CosmosDB persistence | `CosmosDbStorage` |

### Two Programming Models

**1. ActivityHandler (inheritance-based)**:
```python
class MyAgent(ActivityHandler):
    async def on_message_activity(self, context: TurnContext):
        await context.send_activity(f"You said: {context.activity.text}")
```

**2. AgentApplication (modern, decorator-based)**:
```python
app = AgentApplication[TurnState]()

@app.message()
async def on_message(context: TurnContext[TurnState]):
    await context.send_activity(f"You said: {context.activity.text}")
```

### Key Runtime Flow

```
HTTP POST /api/messages
  ↓
Web Framework (aiohttp/FastAPI)
  ↓
CloudAdapter.process()
  ↓
Parse Activity JSON → Create ClaimsIdentity
  ↓
ChannelServiceAdapter.process_activity()
  ↓
Create TurnContext(adapter, activity, identity)
  ↓
Middleware Pipeline (auth, logging, etc.)
  ↓
Agent.on_turn(context)
  ↓
Route to handler (ActivityHandler methods OR AgentApplication selectors)
  ↓
Handler executes, may call context.send_activity()
  ↓
Middleware unwind → Return response
```

### State Management

Three state scopes managed via `TurnContext.state`:

- **ConversationState**: Persisted per conversation (`conversation[conversation_id]`)
- **UserState**: Persisted per user across conversations (`user[user_id]`)
- **TempState**: Ephemeral, exists only for the current turn

State is automatically loaded at turn start and saved at turn end using the configured `Storage` implementation.

### Routing System (AgentApplication)

The `AgentApplication` routing system prioritizes activities in this order:

1. **Invoke activities** (Adaptive Cards, task modules)
2. **Agentic requests** (agent-to-agent communication)
3. **Regular messages** (user messages)

Routes are matched using selectors:
- Activity type matching (`activity_types=["message"]`)
- Regex patterns (`message(r"^hello")`)
- Custom selector functions

### Authentication Flow

MSAL-based authentication supports three flows:
1. **User auth**: OAuth for user-to-agent
2. **Agentic user auth**: OAuth for agent-to-agent with user context
3. **Connector auth**: Service-to-service authentication

OAuth state machine:
```
User requests auth → Save _SignInState → Send OAuthCard
  → User completes OAuth → Token callback → Retrieve token
  → Resume conversation with auth
```

### Channel Service Clients

The SDK dynamically selects the appropriate client based on channel context:

- **Teams**: `TeamsConnectorClient` with Teams-specific APIs
- **Copilot Studio (MCS)**: `McsConnectorClient` with Direct-to-Engine
- **Generic**: `BotFrameworkConnectorClient` for standard channels

Factory pattern in `RestChannelServiceClientFactory` handles this selection.

## Important Architectural Patterns

### Protocol-Oriented Design
All major abstractions use Python Protocols (structural typing) for loose coupling:
- `Agent`, `TurnContextProtocol`, `ChannelAdapterProtocol`, `Storage`

### Adapter Pattern
- Framework adapters translate framework-specific types to SDK protocols
- `HttpRequestProtocol` abstracts HTTP request details
- `ChannelServiceAdapter` adapts between SDK and channel services

### Middleware Pipeline
Cross-cutting concerns (auth, logging, state management) implemented as middleware:
```python
MiddlewareSet → Middleware 1 → ... → Agent Handler → Unwind
```

### Factory Pattern
- `ChannelServiceClientFactory`: Creates appropriate clients
- `MessageFactory`, `CardFactory`: Builders for creating messages

## Code Style and Conventions

- **Formatting**: `black` with 88-character line length (not 127 for flake8)
- **Linting**: `flake8` with max line length 127, max complexity 10
- **Type hints**: Heavy use of generics and protocols
- **Async-first**: All I/O operations are async
- **Pydantic models**: Activity protocol uses Pydantic for validation
- **Error resources**: Standardized error codes with help URLs in `errors/` subdirectories

## Testing Agents Locally

### Prerequisites
1. Install [Microsoft Dev Tunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started):
   ```bash
   winget install Microsoft.devtunnel
   ```

2. Create and run tunnel:
   ```bash
   devtunnel user login
   devtunnel create my-tunnel -a
   devtunnel port create -p 3978 my-tunnel
   devtunnel host -a my-tunnel
   ```
   Record the tunnel URL for configuration.

3. Install [M365 Agents Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit):
   ```bash
   winget install --id=Microsoft.M365AgentsPlayground -e
   ```

### Running Samples

Samples are in `test_samples/`:
- `app_style/`: Examples using `AgentApplication`
- `teams_agent/`: Teams-specific agent
- `fastapi/`: FastAPI integration example
- `agent_to_agent/`: Agent-to-agent communication

Run samples from VS Code or directly:
```bash
cd test_samples/app_style
python empty_agent.py
```

## File Organization

```
libraries/
  microsoft-agents-activity/
  microsoft-agents-hosting-core/
  microsoft-agents-authentication-msal/
  microsoft-agents-hosting-{aiohttp,fastapi,teams}/
  microsoft-agents-storage-{blob,cosmos}/
  microsoft-agents-copilotstudio-client/

tests/
  {package-name}/  # Tests organized by package

test_samples/
  app_style/       # AgentApplication examples
  teams_agent/     # Teams examples
  fastapi/         # FastAPI examples
  agent_to_agent/  # Agent-to-agent examples

scripts/
  dev_setup.sh     # Linux/macOS dev setup
  dev_setup.ps1    # Windows dev setup

versioning/
  pyproject.toml   # Centralized version management
```

## Common Pitfalls

1. **Import structure**: Use `microsoft_agents` (underscores), not `microsoft.agents` (dots)
2. **Editable installs**: Always use `--config-settings editable_mode=compat` for editable installs
3. **Async everywhere**: All I/O operations are async, don't forget `await`
4. **State persistence**: State is auto-saved only if `Storage` is configured
5. **Activity responses**: Not all activities require a response (200), some return 202 Accepted
6. **Turn lifetime**: `TurnContext` is scoped to a single turn, don't cache it
7. **Middleware order**: Middleware runs in registration order, reverse on unwind

## Debugging

The SDK includes source code for debugging. Key areas for breakpoints:

- **Request entry**: `CloudAdapter.process()` in hosting adapters
- **Activity parsing**: `ChannelServiceAdapter.process_activity()`
- **Turn context creation**: `TurnContext.__init__()`
- **Routing**: `AgentApplication._on_turn()` or `ActivityHandler.on_turn()`
- **State management**: `TurnState.load()` and `save()`
- **Activity sending**: `TurnContext.send_activity()`
- **Connector calls**: `ConnectorClient` methods in hosting-core

## Release Process

Versioning is centralized in `versioning/pyproject.toml` using `setuptools-git-versioning`. All packages share the same version number for consistency.
