# Microsoft Agents Hosting MCP

MCP (Model Context Protocol) hosting adapter for the Microsoft 365 Agents SDK.

This package enables exposing an M365 Agent as an MCP server, allowing MCP
clients (such as language models and AI assistants) to discover and invoke the
agent's capabilities through the standard MCP protocol.

## Installation

```bash
pip install microsoft-agents-hosting-mcp
```

## Usage

```python
from microsoft_agents.hosting.mcp import MCPAdapter

# Create adapter with your agent
adapter = MCPAdapter(agent=my_agent)

# Mount on FastAPI
app.mount("/mcp", adapter.streamable_http_app())
```
