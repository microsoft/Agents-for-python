import os

import uvicorn
from fastapi import FastAPI, Request

from microsoft_agents.hosting.fastapi import (
    start_agent_process,
    jwt_authorization_decorator,
)

from .agent import AGENT_APP, CONNECTION_MANAGER


if __name__ == "__main__":

    app = FastAPI(title="Empty Agent Sample", version="1.0.0")
    app.state.agent_configuration = (
        CONNECTION_MANAGER.get_default_connection_configuration()
    )


    @app.post("/api/messages")
    @jwt_authorization_decorator
    async def messages_handler(
        request: Request,
    ):
        """Main endpoint for processing bot messages."""

        return await start_agent_process(
            request,
            AGENT_APP,
            AGENT_APP.adapter,
        )

    port = int(os.environ.get("PORT", 3978))
    uvicorn.run(app, host="127.0.0.1", port=port)
