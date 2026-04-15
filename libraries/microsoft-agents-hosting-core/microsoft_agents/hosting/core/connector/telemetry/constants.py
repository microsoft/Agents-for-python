# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

SPAN_REPLY_TO_ACTIVITY = "agents.connector.reply_to_activity"
SPAN_SEND_TO_CONVERSATION = "agents.connector.send_to_conversation"
SPAN_UPDATE_ACTIVITY = "agents.connector.update_activity"
SPAN_DELETE_ACTIVITY = "agents.connector.delete_activity"
SPAN_CREATE_CONVERSATION = "agents.connector.create_conversation"
SPAN_GET_CONVERSATIONS = "agents.connector.get_conversations"
SPAN_GET_CONVERSATION_MEMBERS = "agents.connector.get_conversation_members"
SPAN_UPLOAD_ATTACHMENT = "agents.connector.upload_attachment"
SPAN_GET_ATTACHMENT = "agents.connector.get_attachment"
SPAN_GET_ATTACHMENT_INFO = "agents.connector.get_attachment_info"

SPAN_GET_USER_TOKEN = "agents.user_token_client.get_user_token"
SPAN_SIGN_OUT = "agents.user_token_client.sign_out"
SPAN_GET_SIGN_IN_RESOURCE = "agents.user_token_client.get_sign_in_resource"
SPAN_EXCHANGE_TOKEN = "agents.user_token_client.exchange_token"
SPAN_GET_TOKEN_OR_SIGN_IN_RESOURCE = (
    "agents.user_token_client.get_token_or_sign_in_resource"
)
SPAN_GET_TOKEN_STATUS = "agents.user_token_client.get_token_status"
SPAN_GET_AAD_TOKENS = "agents.user_token_client.get_aad_tokens"

METRIC_CONNECTOR_REQUEST_COUNT = "agents.connector.request.count"
METRIC_CONNECTOR_REQUEST_DURATION = "agents.connector.request.duration"

METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT = "agents.user_token_client.request.count"
METRIC_USER_TOKEN_CLIENT_REQUEST_DURATION = "agents.user_token_client.request.duration"
