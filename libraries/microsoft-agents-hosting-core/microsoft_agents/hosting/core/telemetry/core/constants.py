# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

from opentelemetry.sdk.resources import Resource

# Telemetry resource information

SERVICE_NAME = "microsoft_agents"
SERVICE_VERSION = "1.0.0"

RESOURCE = Resource.create(
    {
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "telemetry.sdk.language": "python",
    }
)

# Span operation names

SPAN_ADAPTER_PROCESS = "agents.adapter.process"
SPAN_ADAPTER_SEND_ACTIVITIES = "agents.adapter.sendActivities"
SPAN_ADAPTER_UPDATE_ACTIVITY = "agents.adapter.updateActivity"
SPAN_ADAPTER_DELETE_ACTIVITY = "agents.adapter.deleteActivity"
SPAN_ADAPTER_CONTINUE_CONVERSATION = "agents.adapter.continueConversation"
SPAN_ADAPTER_CREATE_CONNECTOR_CLIENT = "agents.adapter.createConnectorClient"
SPAN_ADAPTER_CREATE_USER_TOKEN_CLIENT = "agents.adapter.createUserTokenClient"

SPAN_APP_ON_TURN = "agents.app.run"
SPAN_APP_ROUTE_HANDLER = "agents.app.routeHandler"
SPAN_APP_BEFORE_TURN = "agents.app.beforeTurn"
SPAN_APP_AFTER_TURN = "agents.app.afterTurn"
SPAN_APP_DOWNLOAD_FILES = "agents.app.downloadFiles"

SPAN_CONNECTOR_REPLY_TO_ACTIVITY = "agents.connector.replyToActivity"
SPAN_CONNECTOR_SEND_TO_CONVERSATION = "agents.connector.sendToConversation"
SPAN_CONNECTOR_UPDATE_ACTIVITY = "agents.connector.updateActivity"
SPAN_CONNECTOR_DELETE_ACTIVITY = "agents.connector.deleteActivity"
SPAN_CONNECTOR_CREATE_CONVERSATION = "agents.connector.createConversation"
SPAN_CONNECTOR_GET_CONVERSATIONS = "agents.connector.getConversations"
SPAN_CONNECTOR_GET_CONVERSATION_MEMBERS = "agents.connector.getConversationMembers"
SPAN_CONNECTOR_UPLOAD_ATTACHMENT = "agents.connector.uploadAttachment"
SPAN_CONNECTOR_GET_ATTACHMENT = "agents.connector.getAttachment"

SPAN_STORAGE_READ = "agents.storage.read"
SPAN_STORAGE_WRITE = "agents.storage.write"
SPAN_STORAGE_DELETE = "agents.storage.delete"

SPAN_TURN_SEND_ACTIVITY = "agents.turn.sendActivity"
SPAN_TURN_UPDATE_ACTIVITY = "agents.turn.updateActivity"
SPAN_TURN_DELETE_ACTIVITY = "agents.turn.deleteActivity"

# Metrics

# counters

METRIC_ACTIVITIES_RECEIVED = "agents.activities.received"
METRIC_ACTIVITIES_SENT = "agents.activities.sent"
METRIC_ACTIVITIES_UPDATED = "agents.activities.updated"
METRIC_ACTIVITIES_DELETED = "agents.activities.deleted"

METRIC_TURN_TOTAL = "agents.turn.total"
METRIC_TURN_ERRORS = "agents.turn.errors"

METRIC_CONNECTOR_REQUESTS_TOTAL = "agents.connector.requests"
METRIC_STORAGE_OPERATION_TOTAL = "agents.storage.operation.total"

# histograms

METRIC_TURN_DURATION = "agents.turn.duration"
METRIC_ADAPTER_PROCESS_DURATION = "agents.adapter.process.duration"
METRIC_CONNECTOR_REQUEST_DURATION = "agents.connector.request.duration"
METRIC_STORAGE_OPERATION_DURATION = "agents.storage.operation.duration"


# Attributes
#
# This section represents a mapping of internal attribute names to standardized telemetry attribute names.
# There are two major reasons for this:
# 1. Consistency with the other SDKs and the docs. Each language/SDK has different conventions for variable naming.
# 2. Flexibility: This mapping allows us to change the internal attribute names without affecting the telemetry data.
# 3. Efficiency: avoid snake case to camel case conversions (or any other convention)

ATTR_ACTIVITY_DELIVERY_MODE = "activity.delivery_mode"
ATTR_ACTIVITY_CHANNEL_ID = "activity.channel_id"
ATTR_ACTIVITY_ID = "activity.id"
ATTR_ACTIVITY_COUNT = "activities.count"
ATTR_ACTIVITY_TYPE = "activity.type"
ATTR_AGENTIC_USER_ID = "agentic.user_id"
ATTR_AGENTIC_INSTANCE_ID = "agentic.instance_id"
ATTR_APP_ID = "agent.app_id"
ATTR_ATTACHMENT_ID = "activity.attachment.id"
ATTR_ATTACHMENT_COUNT = "activity.attachments.count"
ATTR_AUTH_SCOPES = "auth.scopes"
ATTR_AUTH_TYPE = "auth.method"

ATTR_CONVERSATION_ID = "activity.conversation.id"

# TODO -> rename to ATTR_IS_AGENTIC
ATTR_IS_AGENTIC_REQUEST = "is_agentic_request"

ATTR_KEY_COUNT = "storage.keys.count"

ATTR_ROUTE_AUTHORIZED = "route.authorized"
ATTR_ROUTE_IS_INVOKE = "route.is_invoke"
ATTR_ROUTE_IS_AGENTIC = "route.is_agentic"
ATTR_ROUTE_MATCHED = "route.matched"

ATTR_SERVICE_URL = "service_url"

ATTR_TOKEN_SERVICE_ENDPOINT = "agents.token_service.endpoint"

# VALUES

UNKNOWN = "unknown"
