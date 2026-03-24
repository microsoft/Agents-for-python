# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# Spans

SPAN_GET_ACCESS_TOKEN = "agents.auth.getAccessToken"
SPAN_ACQUIRE_TOKEN_ON_BEHALF_OF = "agents.auth.acquireTokenOnBehalfOf"
SPAN_GET_AGENTIC_INSTANCE_TOKEN = "agents.auth.getAgenticInstanceToken"
SPAN_GET_AGENTIC_USER_TOKEN = "agents.auth.getAgenticUserToken"

# Metrics

METRIC_AUTH_TOKEN_REQUEST_DURATION = "agents.auth.token.request.duration"
METRIC_AUTH_TOKEN_REQUEST_COUNT = "agents.auth.token.request.count"

AUTH_METHOD_OBO = "obo"
AUTH_METHOD_AGENTIC_INSTANCE = "agentic_instance"
AUTH_METHOD_AGENTIC_USER = "agentic_user"