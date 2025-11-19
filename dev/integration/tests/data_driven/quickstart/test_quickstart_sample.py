from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ....samples import QuickstartSample

@ddt("tests/data_driven/quickstart/directline")
class TestQuickstartDirectline(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment