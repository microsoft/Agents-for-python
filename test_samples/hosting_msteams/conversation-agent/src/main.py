# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agent import AGENT_APP, ADAPTER, agents_sdk_config
from .start_server import start_server

if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        adapter=ADAPTER,
        config=agents_sdk_config,
    )
