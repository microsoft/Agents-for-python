import pytest

from microsoft_agents.testing import (
    ddt,
    Integration,
)


# @ddt("tests/data_driven/claire_bot/directline")
# @ddt("tests/data_driven/claire_bot/webchat")
# @ddt("tests/data_driven/claire_bot/msteams")
@pytest.mark.skipif(True, reason="Skipping external agent tests for now.")
class TestClaireBotDirectline(Integration): ...


@ddt("tests/data_driven/claire_bot/directline", prefix="directline")
@ddt("tests/data_driven/claire_bot/webchat", prefix="webchat")
@ddt("tests/data_driven/claire_bot/msteams", prefix="msteams")
class TestClaireBot(Integration):
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = "agents/claire_bot/python/.env"
