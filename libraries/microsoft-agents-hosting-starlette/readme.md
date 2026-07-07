# Microsoft Agents Hosting Starlette

This library provides [Starlette](https://www.starlette.io/) integration for Microsoft Agents, enabling you to
build conversational agents using the Starlette ASGI framework (or any framework built on it).

It mirrors the `microsoft-agents-hosting-fastapi` integration but depends only on Starlette, so it can be used
directly with a bare Starlette application or embedded by other Starlette-based hosts.

## Installation

```bash
pip install microsoft-agents-hosting-starlette
```

## Usage

```python
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from microsoft_agents.hosting.core import AgentApplication, TurnState
from microsoft_agents.hosting.starlette import (
    CloudAdapter,
    JwtAuthorizationMiddleware,
    start_agent_process,
)

# Build your AgentApplication + adapter as usual.
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AGENT_APP: AgentApplication = ...


async def messages(request: Request) -> Response:
    return await start_agent_process(request, AGENT_APP, ADAPTER)


app = Starlette(
    routes=[Route("/api/messages", messages, methods=["POST"])],
)
app.add_middleware(JwtAuthorizationMiddleware)
app.state.agent_configuration = AGENT_APP.auth_configuration
```
