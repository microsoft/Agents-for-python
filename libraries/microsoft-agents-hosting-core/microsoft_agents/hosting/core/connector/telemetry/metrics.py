# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import agents_telemetry
from . import constants

connector_request_count = agents_telemetry.meter.create_counter(
    constants.METRIC_CONNECTOR_REQUEST_COUNT,
    "request",
    description="Total number of connector requests made by the ConnectorClient",
)

connector_request_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_CONNECTOR_REQUEST_DURATION,
    "ms",
    description="Duration of connector requests in milliseconds",
)

user_token_client_request_count = agents_telemetry.meter.create_counter(
    constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT,
    "request",
    description="Total number of user token client requests made by the UserTokenClient",
)

user_token_client_request_duration = agents_telemetry.meter.create_histogram(
    constants.METRIC_USER_TOKEN_CLIENT_REQUEST_DURATION,
    "ms",
    description="Duration of user token client requests in milliseconds",
)