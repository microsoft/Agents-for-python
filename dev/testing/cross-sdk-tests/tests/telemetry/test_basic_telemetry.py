import pytest

from tests._common import (
    create_scenario,
    SDKVersion,
)

AGENT_NAME = "quickstart"
PYTHON_SCENARIO = create_scenario(AGENT_NAME, SDKVersion.PYTHON)
NET_SCENARIO = create_scenario(AGENT_NAME, SDKVersion.NET)
JS_SCENARIO = create_scenario(AGENT_NAME, SDKVersion.JS)

class BaseTelemetryTests:
    def test_telemetry(self, agent_client):
        # This is a placeholder test. The actual telemetry tests will be implemented here.
        assert True

@pytest.mark.agent_test(PYTHON_SCENARIO)
class TestPythonTelemetry(BaseTelemetryTests):
    pass

@pytest.mark.agent_test(NET_SCENARIO)
class TestNetTelemetry(BaseTelemetryTests):
    pass

@pytest.mark.agent_test(JS_SCENARIO)
class TestJSTelemetry(BaseTelemetryTests):
    pass