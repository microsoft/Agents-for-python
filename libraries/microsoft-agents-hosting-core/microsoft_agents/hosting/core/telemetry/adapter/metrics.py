# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

adapter_process_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_ADAPTER_PROCESS_DURATION,
    "ms",
    description="Duration of adapter processing in milliseconds",
)

activities_received = agents_telemetry.meter.create_counter(
    constants.METRIC_ACTIVITIES_RECEIVED,
    description="Number of activities received by the adapter",
)

activities_sent = agents_telemetry.meter.create_counter(
    constants.METRIC_ACTIVITIES_SENT,
    description="Number of activities sent by the adapter",
)

activities_updated = agents_telemetry.meter.create_counter(
    constants.METRIC_ACTIVITIES_UPDATED,
    description="Number of activities updated by the adapter",
)

activities_deleted = agents_telemetry.meter.create_counter(
    constants.METRIC_ACTIVITIES_DELETED,
    description="Number of activities deleted by the adapter",
)
