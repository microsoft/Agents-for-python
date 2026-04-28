# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test helpers for dialog tests. Provides a TestAdapter/TestFlow compatibility
layer that wraps MockTestingAdapter with the old botbuilder-style chained
send/assert_reply API.
"""

from typing import Callable, Union, Awaitable

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    TokenResponse,
    SignInResource,
    TokenOrSignInResourceResponse,
)
from microsoft_agents.hosting.core import ChannelAdapter, TurnContext
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from tests._common.testing_objects import MockTestingAdapter

AgentCallbackHandler = Callable[["TurnContext"], Awaitable[None]]


class _MockUserToken:
    """Mock user_token API for dialog tests."""

    def __init__(self, store: dict, exchange_store: dict, throw_on_exchange: dict):
        self._store = store
        self._exchange_store = exchange_store
        self._throw_on_exchange = throw_on_exchange

    @staticmethod
    def _key(connection_name, channel_id, user_id):
        return f"{connection_name}:{channel_id}:{user_id}"

    @staticmethod
    def _exchange_key(connection_name, channel_id, user_id, item):
        return f"{connection_name}:{channel_id}:{user_id}:{item}"

    async def get_token(self, user_id, connection_name, channel_id, code=None):
        key = self._key(connection_name, channel_id, user_id)
        entry = self._store.get(key)
        if entry:
            token, stored_code = entry
            if stored_code is None or (code is not None and code == stored_code):
                return TokenResponse(
                    connection_name=connection_name,
                    token=token,
                    channel_id=channel_id,
                )
        return None

    async def sign_out(self, user_id, connection_name, channel_id):
        key = self._key(connection_name, channel_id, user_id)
        self._store.pop(key, None)

    async def exchange_token(self, user_id, connection_name, channel_id, body=None):
        token = (body or {}).get("token") or (body or {}).get("uri")
        key = self._exchange_key(connection_name, channel_id, user_id, token or "")
        if key in self._throw_on_exchange:
            raise Exception("Token exchange not allowed for this item.")
        result = self._exchange_store.get(key)
        if result:
            return TokenResponse(
                connection_name=connection_name,
                token=result,
                channel_id=channel_id,
            )
        return None

    async def _get_token_or_sign_in_resource(
        self, user_id, connection_name, channel_id, state, *_
    ):
        key = self._key(connection_name, channel_id, user_id)
        entry = self._store.get(key)
        if entry:
            token, stored_code = entry
            if stored_code is None:
                return TokenOrSignInResourceResponse(
                    token_response=TokenResponse(
                        connection_name=connection_name,
                        token=token,
                        channel_id=channel_id,
                    )
                )
        return TokenOrSignInResourceResponse(
            sign_in_resource=SignInResource(
                sign_in_link=f"https://token.botframework.com/oauthcards?state={state or ''}"
            )
        )


class _MockAgentSignIn:
    """Mock agent_sign_in API for dialog tests."""

    async def get_sign_in_resource(self, state=None):
        return SignInResource(
            sign_in_link=f"https://token.botframework.com/oauthcards?state={state or ''}",
        )


class DialogUserTokenClient:
    """
    A lightweight UserTokenClient mock for dialog tests.
    Implements the user_token and agent_sign_in APIs used by _UserTokenAccess.
    """

    def __init__(self):
        self._store = {}
        self._exchange_store = {}
        self._throw_on_exchange = {}
        self.user_token = _MockUserToken(
            self._store, self._exchange_store, self._throw_on_exchange
        )
        self.agent_sign_in = _MockAgentSignIn()

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str = None,
    ):
        key = f"{connection_name}:{channel_id}:{user_id}"
        self._store[key] = (token, magic_code)

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ):
        key = f"{connection_name}:{channel_id}:{user_id}:{exchangeable_item}"
        self._exchange_store[key] = token

    def throw_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ):
        key = f"{connection_name}:{channel_id}:{user_id}:{exchangeable_item}"
        self._throw_on_exchange[key] = True


class TestFlow:
    """
    Provides a fluent interface for sending messages and asserting replies
    in dialog tests.
    """

    def __init__(self, adapter: "DialogTestAdapter", callback: AgentCallbackHandler):
        self._adapter = adapter
        self._callback = callback

    async def send(self, msg: Union[str, Activity]) -> "TestFlow":
        """Send a message or activity to the agent."""
        import asyncio as _asyncio

        # Small delay to ensure time-based timeouts (e.g. OAuthPrompt timeout=1ms) can fire.
        await _asyncio.sleep(0.002)
        self._adapter.active_queue.clear()
        if isinstance(msg, str):
            await self._adapter.send_text_to_agent_async(msg, self._callback)
        else:
            await self._adapter.process_activity_async(msg, self._callback)
        return TestFlow(self._adapter, self._callback)

    async def assert_reply(
        self, expected: Union[str, Activity, Callable, None] = None
    ) -> "TestFlow":
        """Assert the next reply matches the expected text, activity, or callable inspector."""
        import inspect

        reply = self._adapter.get_next_reply()
        if expected is not None:
            if callable(expected) and not isinstance(expected, (str, Activity)):
                # Inspector callable: (activity, description) -> bool (sync or async)
                result = expected(reply, None)
                if inspect.isawaitable(result):
                    result = await result
                assert (
                    result is not False
                ), f"Inspector returned False for reply: {reply}"
            elif isinstance(expected, str):
                assert reply is not None, f"Expected reply '{expected}' but got None"
                assert (
                    reply.text == expected
                ), f"Expected reply text '{expected}' but got '{reply.text}'"
            elif isinstance(expected, Activity):
                assert reply is not None, "Expected a reply but got None"
                if expected.text:
                    assert (
                        reply.text == expected.text
                    ), f"Expected reply text '{expected.text}' but got '{reply.text}'"
                if expected.type:
                    assert (
                        reply.type == expected.type
                    ), f"Expected activity type '{expected.type}' but got '{reply.type}'"
        return TestFlow(self._adapter, self._callback)


class DialogTestAdapter(MockTestingAdapter):
    """
    A test adapter compatible with the botbuilder TestAdapter API.
    Provides send() and assert_reply() methods for fluent test flows.
    Also provides a proper UserTokenClient in turn_state for OAuthPrompt tests.
    """

    def __init__(self, callback: AgentCallbackHandler = None, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback
        # Dialog-specific token client that implements the user_token API
        self._dialog_token_client = DialogUserTokenClient()
        # OAuthPrompt reads claims["aud"] from the identity in turn_state
        self.claims_identity = ClaimsIdentity({"aud": "test-app-id"}, True)

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str = None,
    ):
        """Store a user token for retrieval by OAuthPrompt."""
        self._dialog_token_client.add_user_token(
            connection_name, channel_id, user_id, token, magic_code
        )
        # Also update the base class token client for compatibility
        super().add_user_token(connection_name, channel_id, user_id, token, magic_code)

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ):
        self._dialog_token_client.add_exchangeable_token(
            connection_name, channel_id, user_id, exchangeable_item, token
        )
        super().add_exchangeable_token(
            connection_name, channel_id, user_id, exchangeable_item, token
        )

    def throw_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ):
        self._dialog_token_client.throw_on_exchange_request(
            connection_name, channel_id, user_id, exchangeable_item
        )
        super().throw_on_exchange_request(
            connection_name, channel_id, user_id, exchangeable_item
        )

    def create_turn_context(
        self, activity: Activity, identity: ClaimsIdentity = None
    ) -> TurnContext:
        """
        Creates a turn context with the dialog token client in turn_state
        so OAuthPrompt can find it via _UserTokenAccess.
        """
        turn_context = super().create_turn_context(activity, identity)
        turn_context.turn_state[ChannelAdapter.USER_TOKEN_CLIENT_KEY] = (
            self._dialog_token_client
        )
        # OAuthPrompt reads claims["aud"] from this identity
        turn_context.turn_state[ChannelAdapter.AGENT_IDENTITY_KEY] = (
            identity or self.claims_identity
        )
        return turn_context

    def make_activity(self, text: str = None) -> Activity:
        """
        Creates a message activity without setting locale, so that prompts'
        default_locale is used when no locale is present in the activity.
        This matches botbuilder TestAdapter behavior.
        """
        from microsoft_agents.activity import ActivityTypes

        activity = Activity(
            type=ActivityTypes.message,
            from_property=self.conversation.user,
            recipient=self.conversation.agent,
            conversation=self.conversation.conversation,
            service_url=self.conversation.service_url,
            id=str(self._next_id),
            text=text,
        )
        self._next_id += 1
        return activity

    async def send(self, msg: Union[str, Activity]) -> TestFlow:
        """Send a message or activity and return a TestFlow for assertions."""
        self.active_queue.clear()
        if isinstance(msg, str):
            await self.send_text_to_agent_async(msg, self._callback)
        else:
            await self.process_activity_async(msg, self._callback)
        return TestFlow(self, self._callback)
