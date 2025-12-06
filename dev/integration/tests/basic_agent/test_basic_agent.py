import pytest

from microsoft_agents.testing import (
    ddt,
    Integration,
)

TEST_BASIC_AGENT = True


@ddt("tests/basic_agent/directline", prefix="directline")
# @ddt("tests/basic_agent/webchat", prefix="webchat")
# @ddt("tests/basic_agent/msteams", prefix="msteams")
@pytest.mark.skipif(
    not TEST_BASIC_AGENT, reason="Skipping external agent tests for now."
)
class TestBasicAgentExternal(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = "agents/basic_agent/python/.env"
