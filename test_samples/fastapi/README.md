# FastAPI Agent Samples

This folder contains FastAPI equivalents of the agent samples from the `app_style` folder.

## Samples

### 1. empty_agent.py
A simple echo agent that responds to messages and provides basic help functionality. This is the FastAPI equivalent of `empty_agent.py`.

**Features:**
- Basic message echoing
- Welcome message for new conversation members
- Help command

### 2. authorization_agent.py
A more complex agent that demonstrates user authentication and authorization using Microsoft Graph and GitHub APIs. This is the FastAPI equivalent of `authorization_agent.py`.

**Features:**
- User authentication with Microsoft Graph and GitHub
- Profile information retrieval
- OAuth flow handling
- Authentication status checking
- Sign-out functionality

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Microsoft Agents libraries:**
   ```bash
   # From the root of the repository
   pip install -e libraries/microsoft-agents-hosting-fastapi
   pip install -e libraries/microsoft-agents-hosting-core
   pip install -e libraries/microsoft-agents-authentication-msal
   pip install -e libraries/microsoft-agents-activity
   ```

3. **Configure environment variables:**
   - Copy `env.TEMPLATE` to `.env`
   - Fill in the required configuration values

## Running the samples

### Empty Agent
```bash
python empty_agent.py
```

### Authorization Agent
```bash
python authorization_agent.py
```

Both agents will start on `http://localhost:3978` by default. You can change the port by setting the `PORT` environment variable.

## Key Differences from aiohttp samples

1. **Framework**: Uses FastAPI instead of aiohttp
2. **Server startup**: Uses uvicorn instead of aiohttp's run_app
3. **Routing**: Uses FastAPI decorators instead of aiohttp router
4. **Middleware**: Uses FastAPI dependency injection for JWT authorization
5. **Request handling**: Uses FastAPI's Request object and dependency system

## API Endpoints

Both samples expose the following endpoints:

- `POST /api/messages` - Main endpoint for processing bot messages
- `GET /api/messages` - Health check endpoint

## Dependencies

The samples use the `microsoft-agents-hosting-fastapi` library which provides:
- `CloudAdapter` - FastAPI-compatible adapter for processing activities
- `start_agent_process` - Function to handle incoming requests
- `jwt_authorization_dependency` - FastAPI dependency for JWT authentication