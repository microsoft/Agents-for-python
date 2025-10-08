# Microsoft Agents Hosting - aiohttp

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/)

Integration library for hosting Microsoft 365 Agents using aiohttp. This library provides HTTP adapters, middleware, and utilities for building web-based agent applications with the popular aiohttp framework.

## What is this?

This library bridges the Microsoft 365 Agents SDK with aiohttp, allowing you to create HTTP endpoints that handle agent conversations. It provides everything you need to host agents as web services, including request processing, authentication, and routing.

## Installation

```bash
pip install microsoft-agents-hosting-aiohttp
```

## Quick Start

### Basic Agent Server

```python
from aiohttp.web import Application, Request, Response, run_app
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter, 
    jwt_authorization_middleware,
    start_agent_process
)
from microsoft_agents.hosting.core import AgentApplication, TurnState, MemoryStorage
from microsoft_agents.authentication.msal import MsalConnectionManager

# Create your agent application
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**config)
adapter = CloudAdapter(connection_manager=connection_manager)
agent_app = AgentApplication[TurnState](
    storage=storage, 
    adapter=adapter, 
    **config
)

# Set up message handler
async def messages(req: Request) -> Response:
    return await start_agent_process(req, agent_app, adapter)

# Create aiohttp application
app = Application(middlewares=[jwt_authorization_middleware])
app.router.add_post("/api/messages", messages)
app["agent_configuration"] = auth_config
app["agent_app"] = agent_app
app["adapter"] = adapter

# Run the server
run_app(app, host="localhost", port=3978)
```

### Simple Echo Agent

```python
from microsoft_agents.hosting.core import AgentApplication, TurnState, TurnContext
from microsoft_agents.hosting.aiohttp import CloudAdapter

# Create minimal agent
agent_app = AgentApplication[TurnState](
    storage=MemoryStorage(), 
    adapter=CloudAdapter()
)

@agent_app.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

# Use the shared start_server helper
from shared import start_server
start_server(agent_app, auth_configuration=None)
```

## Core Components

### CloudAdapter

The main adapter for processing HTTP requests and converting them to agent activities:

```python
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

# Basic setup
adapter = CloudAdapter(connection_manager=connection_manager)

# With custom error handling
async def custom_error_handler(context, error):
    print(f"Error: {error}")
    await context.send_activity("Sorry, something went wrong.")

adapter.on_turn_error = custom_error_handler

# Process incoming requests
async def handle_messages(request: Request) -> Response:
    return await adapter.process(request, your_agent)
```

### JWT Authorization Middleware

Automatic JWT token validation for secure agent endpoints:

```python
from microsoft_agents.hosting.aiohttp import (
    jwt_authorization_middleware,
    jwt_authorization_decorator
)

# As middleware (recommended)
app = Application(middlewares=[jwt_authorization_middleware])

# As decorator for specific routes
@jwt_authorization_decorator
async def protected_endpoint(request):
    claims = request["claims_identity"]
    return Response(text=f"Hello {claims.name}")
```

### Channel Service Routing

For agent-to-agent communication:

```python
from microsoft_agents.hosting.aiohttp import channel_service_route_table

# Add agent-to-agent routes
app.router.add_routes(
    channel_service_route_table(your_agent, "/api/botresponse")
)
```

## Authentication Setup

### Environment Configuration

```bash
# Required for authentication
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-client-secret
```

### Full Setup with Authentication

```python
import os
from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication, Authorization

load_dotenv()
config = load_configuration_from_env(os.environ)

# Set up authentication and storage
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**config)
adapter = CloudAdapter(connection_manager=connection_manager)
authorization = Authorization(storage, connection_manager, **config)

# Create authenticated agent application
agent_app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter, 
    authorization=authorization,
    **config
)
```

## Advanced Features

### Streaming Responses

Support for real-time streaming responses:

```python
from microsoft_agents.hosting.aiohttp import StreamingResponse, Citation

# Create streaming response with citations
citations = [Citation(content="Source info", title="Reference")]
response = StreamingResponse(citations=citations)

# Use in your agent logic
async def stream_response(context: TurnContext):
    # Stream data to user in real-time
    await context.send_activity("Starting stream...")
    # Implementation depends on your streaming needs
```

### Custom Middleware

Add your own middleware for logging, analytics, etc:

```python
from aiohttp.web import middleware

@middleware
async def logging_middleware(request, handler):
    print(f"Incoming request: {request.method} {request.path}")
    response = await handler(request)
    print(f"Response status: {response.status}")
    return response

app = Application(middlewares=[
    logging_middleware,
    jwt_authorization_middleware
])
```

### Error Handling

Customize error responses:

```python
from microsoft_agents.hosting.core import MessageFactory

async def custom_error_handler(context: TurnContext, error: Exception):
    if isinstance(error, PermissionError):
        await context.send_activity(
            MessageFactory.text("You don't have permission for this action")
        )
    else:
        await context.send_activity(
            MessageFactory.text("An unexpected error occurred")
        )
    
    # Send trace for debugging
    await context.send_trace_activity(
        "Error", str(error), "error", "OnTurnError"
    )

adapter.on_turn_error = custom_error_handler
```

## Integration Patterns

### Teams Integration

```python
from microsoft_agents.hosting.teams import TeamsActivityHandler

class MyTeamsAgent(TeamsActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Hello from Teams!")

# Use with CloudAdapter
agent = MyTeamsAgent()
adapter = CloudAdapter(connection_manager=connection_manager)
```

### Multi-Agent Systems

```python
# Agent 1 - Initiator
app.router.add_routes(
    channel_service_route_table(agent1, "/api/agent1")
)

# Agent 2 - Responder  
app.router.add_routes(
    channel_service_route_table(agent2, "/api/agent2")
)

# Configure agent communication
from microsoft_agents.hosting.core import HttpAgentChannelFactory

channel_factory = HttpAgentChannelFactory()
# Set up agent discovery and routing
```

### Development vs Production

```python
# Development - simpler setup
if os.getenv("ENVIRONMENT") == "development":
    adapter = CloudAdapter()  # Anonymous mode
else:
    # Production - full authentication
    adapter = CloudAdapter(connection_manager=connection_manager)
```

## Testing Your Agent

```python
import aiohttp
import asyncio

async def test_agent():
    async with aiohttp.ClientSession() as session:
        # Test message
        activity = {
            "type": "message",
            "text": "Hello agent!",
            "conversation": {"id": "test-conversation"},
            "from": {"id": "test-user"},
            "recipient": {"id": "test-agent"}
        }
        
        async with session.post(
            "http://localhost:3978/api/messages",
            json=activity,
            headers={"Content-Type": "application/json"}
        ) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                result = await response.json()
                print(f"Response: {result}")

# Run test
asyncio.run(test_agent())
```

## Key Classes

- **`CloudAdapter`** - Main HTTP adapter for processing agent requests
- **`start_agent_process`** - Helper function to start agent processing
- **`jwt_authorization_middleware`** - JWT authentication middleware
- **`channel_service_route_table`** - Routes for agent-to-agent communication
- **`StreamingResponse`** - Support for streaming responses

## Features

✅ **HTTP hosting** - Full aiohttp integration for web hosting  
✅ **JWT authentication** - Built-in security with middleware  
✅ **Agent-to-agent** - Support for multi-agent communication  
✅ **Streaming** - Real-time response streaming  
✅ **Error handling** - Comprehensive error management  
✅ **Development friendly** - Hot reload and debugging support

## Requirements

- Python 3.9+
- aiohttp 3.11.11+
- Microsoft Agents hosting core library

## Best Practices

1. **Use middleware** for cross-cutting concerns like auth and logging
2. **Handle errors gracefully** with custom error handlers
3. **Secure your endpoints** with JWT middleware in production
4. **Structure routes** logically for agent communication
5. **Test thoroughly** with both unit and integration tests

## Need Help?

- 📖 [Full SDK Documentation](https://aka.ms/agents)
- 🌐 [aiohttp Documentation](https://docs.aiohttp.org/)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
- 💡 [Sample Applications](https://github.com/microsoft/Agents-for-python/tree/main/test_samples)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.