# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import path
from dotenv import load_dotenv

from .agent import AGENT_APP, CONNECTION_MANAGER
from .start_server import start_server

load_dotenv(path.join(path.dirname(__file__), ".env"))

# Create and start the agent
if __name__ == "__main__":
    # Use the start_server function from shared module
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )