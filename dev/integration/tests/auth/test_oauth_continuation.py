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
    TokenExchangeRequest,
    TokenResponse,
)
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.hosting.testing import (
    ActivityTemplate,
    AgentClient,
    AgentEnvironment,
    AiohttpScenario,
    ClientConfig,
    ScenarioConfig,
)
from microsoft_agents.hosting.testing import MockUserTokenClient

_APP_ID = "test-app-id"
_CONVERSATION_ID = "auth-continuation-conversation"
_ORIGINAL_TEXT = "slow auth continuation"
_REPLAY_REPLY = f"processed: {_ORIGINAL_TEXT}"
_HANDLER_DELAY_SECONDS = 0.75
_TOKEN_EXCHANGE_ID = "token-exchange-id"
_OAUTH_CONNECTION_NAME = "test-oauth-connection"


class _AuthFlowTestState:
    def reset(self) -> None:
        self.exchange_requests = []
        self.get_token_or_sign_in_calls = []
        self.replay_started = asyncio.Event()
        self.replay_completed = asyncio.Event()
        self.replayed_activity: Activity | None = None
        self.replayed_claims: dict[str, str] | None = None


_auth_flow = _AuthFlowTestState()
_auth_flow.reset()


def _create_user_token_client(
    state: _AuthFlowTestState,
) -> MockUserTokenClient:
    client = MockUserTokenClient()
    client.add_exchangeable_token(
        connection_name=_OAUTH_CONNECTION_NAME,
        channel_id=Channels.ms_teams,
        user_id="user-id",
        exchangeable_item="sso-token",
        token="exchanged-token",
    )

    get_sign_in_resource = client.get_sign_in_resource

    async def get_sign_in_resource_with_fixed_exchange_id(
        connection_name: str,
        activity: Activity,
        final_redirect: str | None = None,
    ):
        resource = await get_sign_in_resource(
            connection_name,
            activity,
            final_redirect,
        )
        resource.token_exchange_resource.id = _TOKEN_EXCHANGE_ID
        return resource

    client.get_sign_in_resource = get_sign_in_resource_with_fixed_exchange_id

    get_token_or_sign_in_resource = client.get_token_or_sign_in_resource

    async def get_token_or_sign_in_resource_with_tracking(
        connection_name: str,
        activity: Activity,
        code: str | None = None,
        final_redirect: str | None = None,
        fwd_url: str | None = None,
    ):
        state.get_token_or_sign_in_calls.append(
            {
                "user_id": activity.from_property.id,
                "connection_name": connection_name,
                "channel_id": activity.channel_id,
            }
        )
        return await get_token_or_sign_in_resource(
            connection_name,
            activity,
            code,
            final_redirect,
            fwd_url,
        )

    client.get_token_or_sign_in_resource = (
        get_token_or_sign_in_resource_with_tracking
    )

    exchange_token = client.exchange_token

    async def exchange_token_with_tracking(
        user_id: str,
        connection_name: str,
        channel_id: str,
        exchange_request: TokenExchangeRequest,
    ) -> TokenResponse:
        state.exchange_requests.append(
            {
                "user_id": user_id,
                "connection_name": connection_name,
                "channel_id": channel_id,
                "body": exchange_request.model_dump(exclude_none=True),
            }
        )
        response = await exchange_token(
            user_id,
            connection_name,
            channel_id,
            exchange_request,
        )
        if response.token:
            client.add_user_token(
                connection_name=connection_name,
                channel_id=channel_id,
                user_id=user_id,
                token=response.token,
            )
        return response

    client.exchange_token = exchange_token_with_tracking
    return client


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
        self._user_token_client = _create_user_token_client(state)

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
    ) -> MockUserTokenClient:
        return self._user_token_client


def init_agent(env: AgentEnvironment):
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

_SCENARIO = AiohttpScenario.create(
    init_agent,
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
