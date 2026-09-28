# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse

from microsoft_agents.hosting.fastapi import (
    jwt_authorization_decorator,
    start_agent_process,
)

from .setup import connections, adapter
from .agent import agent

_STATIC_DIR = Path(__file__).parent.parent / "static"

if __name__ == "__main__":
    app = FastAPI(title="Demo Agent", version="1.0.0")
    app.state.agent_configuration = connections.get_default_connection()

    @app.post("/api/messages")
    @jwt_authorization_decorator
    async def entry_point(request: Request):
        """Handle incoming messages from the client."""
        return (
            await start_agent_process(request, agent, adapter)
        ) or Response(status_code=500)

    @app.get("/settings", response_class=FileResponse)
    async def serve_settings(_: Request) -> FileResponse:
        """Serve the settings HTML file."""
        return FileResponse(_STATIC_DIR / "settings.html")

    @app.get("/api/messages")
    async def health_check(_: Request) -> Response:
        """Health check endpoint."""
        return Response(status_code=200)

    uvicorn.run(app, host="127.0.0.1", port=int(environ.get("PORT", 3978)))