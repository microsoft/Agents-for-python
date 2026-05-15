# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

ms_agents_logger = logging.getLogger("microsoft_agents")
ms_agents_logger.addHandler(logging.StreamHandler())
ms_agents_logger.setLevel(logging.INFO)

from .agent import APP  # noqa: E402  (side-effect imports register routes)
from .app import CONNECTION_MANAGER  # noqa: E402
from .start_server import start_server  # noqa: E402

start_server(
    agent_application=APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
