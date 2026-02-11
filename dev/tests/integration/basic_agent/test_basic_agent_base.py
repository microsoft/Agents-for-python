from microsoft_agents.testing.core.external_scenario import ExternalScenario
import pytest

from microsoft_agents.testing import (
    ActivityTemplate,
    ClientConfig,
    ExternalScenario,
    ScenarioConfig,
)

_TEMPLATE = ActivityTemplate({
    "channel_id": "directline",
    "locale": "en-US",
    "conversation.id": "conv1",
    "from.id": "user1",
    "from.name": "User",
    "recipient.id": "bot",
    "recipient.name": "Bot",
})

_SCENARIO = ExternalScenario(
    "http://localhost:3978/api/messages/",
    config=ScenarioConfig(
        client_config=ClientConfig(
            activity_template=_TEMPLATE
        )
    )
)

@pytest.mark.skip(reason="Base class for other tests")
@pytest.mark.agent_test(_SCENARIO, agent_name="basic-agent")
class TestBasicAgentBase:
    """Base test class for basic agent."""