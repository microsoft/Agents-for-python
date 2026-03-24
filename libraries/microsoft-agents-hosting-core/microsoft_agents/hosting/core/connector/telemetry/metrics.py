# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

connector_request_total = agents_telemetry.meter.create_counter(
    constants.METRIC_REQUESTS_TOTAL,
    "request",
    description="Total number of connector requests made by the agent",
)

connector_request_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_REQUEST_DURATION,
    "ms",
    description="Duration of connector requests in milliseconds",
)
