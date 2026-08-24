import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    ApplicationOptions,
    Authorization,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.proactive import ProactiveOptions
from microsoft_agents.hosting.core.app.proactive.telemetry import constants
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.testing import AgentEnvironment, AiohttpScenario

from ..utils.telemetry_fixtures import (  # noqa: F401
    test_exporter,
    test_telemetry,
)


class _FakeTokenProvider:
    def __init__(self) -> None:
        self._configuration = AgentAuthConfiguration()

    @property
    def configuration(self) -> AgentAuthConfiguration:
        return self._configuration

    async def get_access_token(
        self,
        resource_url: str,
        scopes: list[str],
        force_refresh: bool = False,
    ) -> str:
        return "test-access-token"


class _FakeConnections:
    def __init__(self) -> None:
        self._provider = _FakeTokenProvider()

    def get_connection(self, connection_name: str):
        return self._provider

    def get_default_connection(self):
        return self._provider

    def get_token_provider(
        self,
        claims_identity: ClaimsIdentity,
        service_url: str,
    ):
        return self._provider

    def get_token_provider_from_activity(
        self,
        claims_identity: ClaimsIdentity,
        activity: Activity,
    ):
        return self._provider

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        return self._provider.configuration


def _create_scenario() -> AiohttpScenario:
    connections = _FakeConnections()
    storage = MemoryStorage()
    adapter = CloudAdapter(connection_manager=connections)
    authorization = Authorization(storage, connections)
    app = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=storage,
            adapter=adapter,
            proactive=ProactiveOptions(),
        ),
        authorization=authorization,
    )

    @app.activity(ActivityTypes.message)
    async def store_conversation(context: TurnContext, state: TurnState) -> None:
        await app.proactive.store_conversation(context)

    environment = AgentEnvironment(
        config={},
        agent_application=app,
        authorization=authorization,
        adapter=adapter,
        storage=storage,
        connections=connections,
    )
    return AiohttpScenario(environment, use_jwt_middleware=False)


_SCENARIO = _create_scenario()


def _get_span(spans, name):
    return next(span for span in spans if span.name == name)


@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_continue_conversation_links_to_stored_context(
    test_exporter,
    agent_client,
    agent_application,
    adapter,
):
    activity = agent_client.template.create(
        {
            "type": ActivityTypes.message,
            "id": "proactive-linking-activity",
        }
    )
    await agent_client.send(activity)

    async def continue_handler(context: TurnContext, state: TurnState) -> None:
        pass

    await agent_application.proactive.continue_conversation(
        adapter,
        activity.conversation.id,
        continue_handler,
    )

    spans = test_exporter.get_finished_spans()
    store_span = _get_span(spans, constants.SPAN_STORE_CONVERSATION)
    continuation_span = _get_span(spans, constants.SPAN_CONTINUE_CONVERSATION)

    assert len(continuation_span.links) == 1
    link_context = continuation_span.links[0].context
    assert link_context.trace_id == store_span.context.trace_id
    assert link_context.span_id == store_span.context.span_id
    assert link_context.trace_flags == store_span.context.trace_flags
    assert link_context.trace_state == store_span.context.trace_state
    assert store_span.context.is_remote is False
    assert link_context.is_remote is True


@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_overwriting_conversation_links_to_latest_store_span(
    test_exporter,
    agent_client,
    agent_application,
    adapter,
):
    conversation_id = "proactive-overwrite-conversation"
    first_activity = agent_client.template.create(
        {
            "type": ActivityTypes.message,
            "id": "first-store-activity",
            "conversation": {"id": conversation_id},
        }
    )
    second_activity = agent_client.template.create(
        {
            "type": ActivityTypes.message,
            "id": "second-store-activity",
            "conversation": {"id": conversation_id},
        }
    )

    await agent_client.send(first_activity)
    await agent_client.send(second_activity)

    async def continue_handler(context: TurnContext, state: TurnState) -> None:
        pass

    await agent_application.proactive.continue_conversation(
        adapter,
        conversation_id,
        continue_handler,
    )

    spans = test_exporter.get_finished_spans()
    store_spans = [
        span for span in spans if span.name == constants.SPAN_STORE_CONVERSATION
    ]
    continuation_span = _get_span(spans, constants.SPAN_CONTINUE_CONVERSATION)

    assert len(store_spans) == 2
    assert len(continuation_span.links) == 1
    link_context = continuation_span.links[0].context
    assert link_context.trace_id == store_spans[-1].context.trace_id
    assert link_context.span_id == store_spans[-1].context.span_id
    assert link_context.trace_id != store_spans[0].context.trace_id
    assert link_context.is_remote is True
