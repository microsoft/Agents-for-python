# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ

import uvicorn
from fastapi import FastAPI

from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
)
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    JwtAuthorizationMiddleware,
    start_agent_process
)

from microsoft_agents.hosting.a2a import add_a2a

def start_server(
    agent_application: AgentApplication,
    auth_configuration: AgentAuthConfiguration,
) -> None:
    """Start the FastAPI server with the given agent application and authentication configuration.
    
    :param agent_application: The agent application to be hosted by the server.
    :param auth_configuration: The authentication configuration for the agent.
    """
    
    app = FastAPI(title="Empty Agent Sample", version="1.0.0")
    app.add_middleware(JwtAuthorizationMiddleware)
    app.state.agent_configuration = (
        auth_configuration.get_default_connection_configuration()
    )

    # Here we set use_jwt_middleware to False because we have already applied this
    # middleware at the app-level above
    add_a2a(app, agent_application, use_jwt_middleware=False) 

    port = int(environ.get("PORT", 3978))
    uvicorn.run(app, host="127.0.0.1", port=port)