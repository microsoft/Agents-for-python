# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import ChannelAdapter, TurnContext
from microsoft_agents.activity import TokenResponse


class TokenExchangeRequest:
    """Simple token exchange request for OAuth flows."""

    def __init__(self, uri: str = None, token: str = None):
        self.uri = uri
        self.token = token


class _UserTokenAccess:
    """
    Internal helper for accessing user token operations through the UserTokenClient
    registered in the turn state.
    """

    @staticmethod
    def _get_user_token_client(context: TurnContext):
        client = context.turn_state.get(ChannelAdapter.USER_TOKEN_CLIENT_KEY)
        if not client:
            raise Exception(
                "OAuth is not supported by the current adapter. "
                "Ensure the adapter provides a UserTokenClient in the turn state."
            )
        return client

    @staticmethod
    async def get_user_token(
        context: TurnContext, settings, magic_code: str = None
    ) -> TokenResponse:
        """
        Get the user's token for the given OAuth connection.
        :param context: The turn context.
        :param settings: OAuthPromptSettings containing connection_name.
        :param magic_code: Optional magic code from the user.
        :return: TokenResponse or None if not signed in.
        """
        user_token_client = _UserTokenAccess._get_user_token_client(context)
        activity = context.activity
        user_id = activity.from_property.id if activity.from_property else None
        channel_id = activity.channel_id

        return await user_token_client.user_token.get_token(
            user_id,
            settings.connection_name,
            channel_id,
            magic_code,
        )

    @staticmethod
    async def sign_out_user(context: TurnContext, settings) -> None:
        """
        Sign the user out of the given OAuth connection.
        :param context: The turn context.
        :param settings: OAuthPromptSettings containing connection_name.
        """
        user_token_client = _UserTokenAccess._get_user_token_client(context)
        activity = context.activity
        user_id = activity.from_property.id if activity.from_property else None
        channel_id = activity.channel_id

        await user_token_client.user_token.sign_out(
            user_id,
            settings.connection_name,
            channel_id,
        )

    @staticmethod
    async def get_sign_in_resource(context: TurnContext, settings):
        """
        Get the sign-in resource (URL + token exchange resource) for the connection.
        :param context: The turn context.
        :param settings: OAuthPromptSettings containing connection_name.
        :return: SignInResource with sign_in_link and token_exchange_resource.
        """
        user_token_client = _UserTokenAccess._get_user_token_client(context)
        activity = context.activity

        # Build a state parameter that encodes enough context for the sign-in flow
        import json
        state = json.dumps(
            {
                "connectionName": settings.connection_name,
                "conversation": {
                    "id": activity.conversation.id if activity.conversation else None,
                    "isGroup": (
                        activity.conversation.is_group
                        if activity.conversation
                        else False
                    ),
                    "conversationType": (
                        activity.conversation.conversation_type
                        if activity.conversation
                        else None
                    ),
                    "tenantId": (
                        activity.conversation.tenant_id
                        if activity.conversation
                        else None
                    ),
                    "name": (
                        activity.conversation.name if activity.conversation else None
                    ),
                },
                "relatesTo": None,
                "MSAppId": settings.ms_app_id if hasattr(settings, "ms_app_id") else None,
            }
        )

        return await user_token_client.agent_sign_in.get_sign_in_resource(state=state)

    @staticmethod
    async def exchange_token(
        context: TurnContext, settings, token_exchange_request
    ) -> TokenResponse:
        """
        Exchange a token using the token exchange request.
        :param context: The turn context.
        :param settings: OAuthPromptSettings containing connection_name.
        :param token_exchange_request: The token exchange request (has .token and .uri).
        :return: TokenResponse or None if exchange failed.
        """
        user_token_client = _UserTokenAccess._get_user_token_client(context)
        activity = context.activity
        user_id = activity.from_property.id if activity.from_property else None
        channel_id = activity.channel_id

        body = {}
        if hasattr(token_exchange_request, "token") and token_exchange_request.token:
            body["token"] = token_exchange_request.token
        if hasattr(token_exchange_request, "uri") and token_exchange_request.uri:
            body["uri"] = token_exchange_request.uri

        return await user_token_client.user_token.exchange_token(
            user_id,
            settings.connection_name,
            channel_id,
            body=body,
        )
