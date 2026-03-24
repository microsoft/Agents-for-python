# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

adapter_process_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_ADAPTER_PROCESS_DURATION,
    "ms",
    description="Duration of adapter processing in milliseconds",
)
