# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

turn_total = agents_telemetry.meter.create_counter(
    constants.METRIC_TURN_TOTAL,
    "turn",
    description="Total number of turns processed by the agent",
)

turn_errors = agents_telemetry.meter.create_counter(
    constants.METRIC_TURN_ERRORS,
    "turn",
    description="Number of turns that resulted in an error",
)

turn_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_TURN_DURATION,
    "ms",
    description="Duration of agent turns in milliseconds",
)
