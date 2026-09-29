# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ

import uvicorn
from fastapi import FastAPI

from microsoft_agents.hosting.a2a import add_a2a

from .a2a import A2A_ADAPTER
from .agent import AGENT


def create_app() -> FastAPI:
    """Create the FastAPI application and register the A2A routes."""

    app = FastAPI(title="SDK A2A Echo Agent", version="1.0.0")

    # Authentication is disabled only to keep this local sample simple.
    add_a2a(
        app,
        AGENT,
        adapter=A2A_ADAPTER,
        use_jwt_middleware=False,
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def start_server(app: FastAPI | None = None) -> None:
    """Start the local A2A server."""

    uvicorn.run(
        app or create_app(),
        host=environ.get("HOST", "127.0.0.1"),
        port=int(environ.get("PORT", "41241")),
    )