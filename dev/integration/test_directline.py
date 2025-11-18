from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from .quickstart_sample import QuickstartSample

@ddt("./data_driven_tests/directline")
class TestDirectLine(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment