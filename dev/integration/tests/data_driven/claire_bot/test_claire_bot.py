import pytest

from microsoft_agents.testing import (
    ddt,
    Integration,
)

@ddt("tests/data_driven/claire_bot/directline")
@ddt("tests/data_driven/claire_bot/webchat")
@ddt("tests/data_driven/claire_bot/msteams")
@pytest.mark.skipif(True, reason="Skipping external agent tests for now.")
class TestClaireBotDirectline(Integration):
    ...