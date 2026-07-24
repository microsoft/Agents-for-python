import asyncio
import time
from pathlib import Path
from typing import Optional

import pytest
from aiohttp import ClientSession

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    ResourceResponse,
    SignInConstants,
    SignInResource,
    TokenExchangeResource,
    TokenOrSignInResourceResponse,
    TokenPostResource,
    TokenResponse,
)
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    ActivityTemplate,
    AgentClient,
    AgentEnvironment,
    AiohttpScenario,
    ClientConfig,
    ScenarioConfig,
)

_APP_ID = "test-app-id"
_CONVERSATION_ID = "auth-continuation-conversation"
_ORIGINAL_TEXT = "slow auth continuation"
_REPLAY_REPLY = f"processed: {_ORIGINAL_TEXT}"
_HANDLER_DELAY_SECONDS = 0.75
_TOKEN_EXCHANGE_ID = "token-exchange-id"
_OAUTH_CONNECTION_NAME = "test-oauth-connection"


class _AuthFlowTestState:
    def reset(self) -> None:
        self.token_available = False
        self.exchange_requests = []
        self.get_token_or_sign_in_calls = []
        self.replay_started = asyncio.Event()
        self.replay_completed = asyncio.Event()
        self.replayed_activity: Activity | None = None
        self.replayed_claims: dict[str, str] | None = None


_auth_flow = _AuthFlowTestState()
_auth_flow.reset()


class _FakeUserToken:
    def __init__(self, state: _AuthFlowTestState):
        self._state = state

    async def get_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: Optional[str] = None,
        code: Optional[str] = None,
    ) -> TokenResponse:
        if self._state.token_available:
            return TokenResponse(
                connection_name=connection_name,
                token="cached-token",
                channel_id=channel_id,
            )
        return TokenResponse()

    async def _get_token_or_sign_in_resource(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        state: str,
        code: str = "",
        final_redirect: str = "",
        fwd_url: str = "",
    ) -> TokenOrSignInResourceResponse:
        self._state.get_token_or_sign_in_calls.append(
            {
                "user_id": user_id,
                "connection_name": connection_name,
                "channel_id": channel_id,
            }
        )
        if self._state.token_available:
            return TokenOrSignInResourceResponse(
                token_response=TokenResponse(
                    connection_name=connection_name,
                    token="cached-token",
                    channel_id=channel_id,
                )
            )
        return TokenOrSignInResourceResponse(
            sign_in_resource=SignInResource(
                sign_in_link="https://example.test/signin",
                token_exchange_resource=TokenExchangeResource(
                    id=_TOKEN_EXCHANGE_ID,
                    uri="api://test-token-exchange",
                    provider_id="test-provider",
                ),
                token_post_resource=TokenPostResource(
                    sas_url="https://example.test/token-post"
                ),
            )
        )

    async def get_aad_tokens(
        self,
        user_id: str,
        connection_name: str,
        channel_id: Optional[str] = None,
        body: Optional[dict] = None,
    ) -> dict[str, TokenResponse]:
        return {}

    async def sign_out(
        self,
        user_id: str,
        connection_name: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> None:
        self._state.token_available = False

    async def get_token_status(
        self,
        user_id: str,
        channel_id: Optional[str] = None,
        include: Optional[str] = None,
    ) -> list:
        return []

    async def exchange_token(
        self,
        user_id: str,
        connection_name: str,
        channel_id: str,
        body: Optional[dict] = None,
    ) -> TokenResponse:
        self._state.exchange_requests.append(
            {
                "user_id": user_id,
                "connection_name": connection_name,
                "channel_id": channel_id,
                "body": body,
            }
        )
        self._state.token_available = True
        return TokenResponse(
            connection_name=connection_name,
            token="exchanged-token",
            channel_id=channel_id,
        )


class _FakeUserTokenClient:
    def __init__(self, state: _AuthFlowTestState):
        self._user_token = _FakeUserToken(state)

    @property
    def user_token(self) -> _FakeUserToken:
        return self._user_token

    @property
    def agent_sign_in(self):
        return None

    async def close(self) -> None:
        return None


class _FakeConversations:
    def __init__(self, service_url: str, session: ClientSession):
        self._service_url = service_url.rstrip("/")
        self._session = session

    async def send_to_conversation(
        self, conversation_id: str, activity: Activity
    ) -> ResourceResponse:
        return await self._post_activity(conversation_id, activity)

    async def reply_to_activity(
        self, conversation_id: str, activity_id: str, activity: Activity
    ) -> ResourceResponse:
        return await self._post_activity(conversation_id, activity, activity_id)

    async def _post_activity(
        self,
        conversation_id: str,
        activity: Activity,
        activity_id: Optional[str] = None,
    ) -> ResourceResponse:
        activity.id = activity.id or f"activity-{time.perf_counter_ns()}"
        suffix = f"/{conversation_id}/activities"
        if activity_id:
            suffix = f"{suffix}/{activity_id}"
        async with self._session.post(
            f"{self._service_url}{suffix}",
            json=activity.model_dump(
                by_alias=True,
                exclude_unset=True,
                exclude_none=True,
                mode="json",
            ),
        ) as response:
            response.raise_for_status()
        return ResourceResponse(id=activity.id)


class _FakeConnectorClient:
    def __init__(self, service_url: str):
        self._session = ClientSession()
        self._conversations = _FakeConversations(service_url, self._session)

    @property
    def base_uri(self) -> str:
        return ""

    @property
    def attachments(self):
        return None

    @property
    def conversations(self) -> _FakeConversations:
        return self._conversations

    async def close(self) -> None:
        await self._session.close()


class _FakeChannelServiceClientFactory:
    def __init__(self, state: _AuthFlowTestState):
        self._user_token_client = _FakeUserTokenClient(state)

    async def create_connector_client(
        self,
        context,
        claims_identity,
        service_url: str,
        audience: str,
        scopes: Optional[list[str]] = None,
        use_anonymous: bool = False,
    ) -> _FakeConnectorClient:
        return _FakeConnectorClient(service_url)

    async def create_user_token_client(
        self,
        context,
        claims_identity,
        use_anonymous: bool = False,
    ) -> _FakeUserTokenClient:
        return self._user_token_client


async def init_agent(env: AgentEnvironment):
    env.adapter._channel_service_client_factory = _FakeChannelServiceClientFactory(
        _auth_flow
    )

    original_process_activity = env.adapter.process_activity

    async def process_activity_with_test_identity(claims_identity, activity, callback):
        claims_identity.claims.setdefault("aud", _APP_ID)
        claims_identity.claims.setdefault("appid", _APP_ID)
        return await original_process_activity(claims_identity, activity, callback)

    env.adapter.process_activity = process_activity_with_test_identity

    app = env.agent_application

    @app.message(_ORIGINAL_TEXT)
    async def message_handler(context: TurnContext, state: TurnState):
        _auth_flow.replayed_activity = context.activity.model_copy(deep=True)
        _auth_flow.replayed_claims = dict(context.identity.claims)
        _auth_flow.replay_started.set()
        await asyncio.sleep(_HANDLER_DELAY_SECONDS)
        await context.send_activity(_REPLAY_REPLY)
        _auth_flow.replay_completed.set()


_TEMPLATE = ActivityTemplate(
    {
        "channel_id": Channels.ms_teams,
        "locale": "en-US",
        "conversation": {"id": _CONVERSATION_ID},
        "from": {"id": "user-id", "name": "User"},
        "recipient": {"id": "agent-id", "name": "Agent"},
    }
)

_SCENARIO = AiohttpScenario(
    init_agent=init_agent,
    config=ScenarioConfig(
        env_file_path=str(Path(__file__).with_name("auth.env")),
        client_config=ClientConfig(activity_template=_TEMPLATE),
    ),
    use_jwt_middleware=False,
)


@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_token_exchange_returns_before_continuation_replay_finishes(
    agent_client: AgentClient,
):
    _auth_flow.reset()

    original_exchange = (await agent_client.ex_send(_ORIGINAL_TEXT))[0]
    original_activity = original_exchange.request

    token_exchange = Activity(
        type=ActivityTypes.invoke,
        name=SignInConstants.token_exchange_operation_name,
        value={
            "id": _TOKEN_EXCHANGE_ID,
            "connectionName": _OAUTH_CONNECTION_NAME,
            "token": "sso-token",
        },
    )

    start = time.perf_counter()
    invoke_response = await agent_client.invoke(token_exchange)
    elapsed = time.perf_counter() - start

    assert invoke_response.status == 200
    assert elapsed < _HANDLER_DELAY_SECONDS / 2
    assert not _auth_flow.replay_completed.is_set()

    await asyncio.wait_for(_auth_flow.replay_completed.wait(), timeout=2.0)

    replies = [
        activity
        for activity in agent_client.history()
        if activity.type == ActivityTypes.message and activity.text == _REPLAY_REPLY
    ]
    assert len(replies) == 1

    assert len(_auth_flow.exchange_requests) == 1
    assert len(_auth_flow.get_token_or_sign_in_calls) >= 2

    assert _auth_flow.replayed_activity.type == ActivityTypes.message
    assert _auth_flow.replayed_activity.text == original_activity.text
    assert _auth_flow.replayed_activity.channel_id == original_activity.channel_id
    assert (
        _auth_flow.replayed_activity.conversation.id
        == original_activity.conversation.id
    )
    assert _auth_flow.replayed_activity.service_url == original_activity.service_url
    assert _auth_flow.replayed_claims["aud"] == _APP_ID
