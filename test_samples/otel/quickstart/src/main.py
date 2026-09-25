# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .telemetry import configure_otel_providers

configure_otel_providers(service_name="quickstart_agent")

from .agent import AGENT_APP, CONNECTION_MANAGER, ADAPTER
from .start_server import start_server

start_server(
    agent_application=AGENT_APP,
    adapter=ADAPTER,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
