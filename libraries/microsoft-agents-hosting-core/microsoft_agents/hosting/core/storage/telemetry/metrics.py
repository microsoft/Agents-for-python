# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

storage_operation_total = agents_telemetry.meter.create_counter(
    constants.METRIC_STORAGE_OPERATION_TOTAL,
    "operation",
    description="Number of storage operations performed by the agent",
)
storage_operation_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_STORAGE_OPERATION_DURATION,
    "ms",
    description="Duration of storage operations in milliseconds",
)
