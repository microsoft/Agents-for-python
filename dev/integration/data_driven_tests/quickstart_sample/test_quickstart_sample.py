from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ...samples.quickstart_sample import QuickstartSample

@ddt("./tests")
class TestDirectLine(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment