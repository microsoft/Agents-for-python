from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ....samples import BasicSample

@ddt("tests/data_driven/basic/directline")
class TestBasicDirectline(Integration):
    _sample_cls = BasicSample
    _environment_cls = AiohttpEnvironment