# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

auth_token_request_count = agents_telemetry.meter.create_counter(
    constants.METRIC_AUTH_TOKEN_REQUEST_COUNT,
    "request",
    description="Total number of auth token requests made by the AuthTokenClient",
)

auth_token_request_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_AUTH_TOKEN_REQUEST_DURATION,
    "ms",
    description="Duration of auth token requests in milliseconds",
)
