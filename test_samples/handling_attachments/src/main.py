import uvicorn
from fastapi import FastAPI, Request

from microsoft_agents.hosting.fastapi import (
    start_agent_process,
    jwt_authorization_decorator,
)

from .agent import AGENT_APP, ADAPTER, agents_sdk_config


if __name__ == "__main__":

    app = FastAPI(title="Handling Attachments Agent", version="1.0.0")
    app.state.agent_configuration = agents_sdk_config

    @app.post("/api/messages")
    @jwt_authorization_decorator
    async def messages_handler(
        request: Request,
    ):
        """Main endpoint for processing bot messages."""

        return await start_agent_process(
            request,
            AGENT_APP,
           ADAPTER,
        )

    port = agents_sdk_config.get_int("PORT", default=3978)
    uvicorn.run(app, host="127.0.0.1", port=port)
