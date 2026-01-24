import pytest

from microsoft_agents.testing import (
    Integration,
)

TEST_BASIC_AGENT = True


@pytest.mark.skipif(
    not TEST_BASIC_AGENT, reason="Skipping external agent tests for now."
)
class TestBasicAgent(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = "agents/basic_agent/python/.env"
